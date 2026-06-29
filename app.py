import http.server
import socketserver
import json
import os
import sys
import asyncio
import webbrowser
import uuid

# Add current directory to path to locate local google package namespace
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load .env file if it exists (zero-dependency env loader)
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(dotenv_path):
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'\"")

from google.antigravity import Agent, LocalAgentConfig

PORT = 8000
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favorites_recipes.json")
SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")

# Session store for active agents
sessions = {}

class LunchboxGenieHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        # Allow CORS for easy development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # Serve the HTML frontend
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
            with open(index_path, "r", encoding="utf-8") as f:
                self.wfile.write(f.read().encode("utf-8"))
            return

        # Fetch Favorites Recipe Log
        elif self.path == "/api/favorites":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if not os.path.exists(DB_FILE):
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump([], f)
            with open(DB_FILE, "r", encoding="utf-8") as f:
                self.wfile.write(f.read().encode("utf-8"))
            return

        # 404 Fallback
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        try:
            payload = json.loads(post_data) if post_data else {}
        except Exception:
            payload = {}

        if self.path == "/api/draft":
            asyncio.run(self.handle_draft(payload))
        elif self.path == "/api/refine":
            asyncio.run(self.handle_refine(payload))
        elif self.path == "/api/approve":
            asyncio.run(self.handle_approve(payload))
        elif self.path == "/api/rate":
            self.handle_rate(payload)
        else:
            self.send_response(404)
            self.end_headers()

    async def handle_draft(self, payload):
        try:
            kids = payload.get("kids", 2)
            age = payload.get("age", "5, 8")
            include = payload.get("include", "")
            avoid = payload.get("avoid", "")

            # Set up Orchestrator system instructions
            system_instruction = (
                "You are the Orchestrator Agent for Lunchbox Genie, a weekly school lunch planner. "
                "Use your skills and subagents (Dietitian) to generate balanced, allergy-safe menus."
            )
            
            config = LocalAgentConfig(
                model="gemini-3.5-flash",
                system_instructions=system_instruction,
                skills_paths=[SKILLS_DIR]
            )
            
            agent = Agent(config=config)
            sessions[agent.conversation_id] = agent
            
            prompt = (
                f"Plan a weekly school lunch menu for {kids} kids (ages {age}). "
                f"Include: {include}. Avoid/Allergies: {avoid}. "
                "Output the menu as a clean markdown table."
            )
            
            response = await agent.chat(prompt)
            plan_text = await response.text()
            
            resp_payload = {
                "conversation_id": agent.conversation_id,
                "plan": plan_text
            }
            if getattr(agent, "fallback_warning", None):
                resp_payload["notification"] = agent.fallback_warning
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp_payload).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    async def handle_refine(self, payload):
        try:
            conv_id = payload.get("conversation_id")
            refinement = payload.get("refinement", "")
            
            agent = sessions.get(conv_id)
            if not agent:
                config = LocalAgentConfig(conversation_id=conv_id, skills_paths=[SKILLS_DIR])
                agent = Agent(config=config)
                sessions[conv_id] = agent
                
            prompt = f"Please refine the menu with this feedback: '{refinement}'"
            response = await agent.chat(prompt)
            plan_text = await response.text()
            
            resp_payload = {
                "plan": plan_text
            }
            if getattr(agent, "fallback_warning", None):
                resp_payload["notification"] = agent.fallback_warning
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp_payload).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    async def handle_approve(self, payload):
        try:
            conv_id = payload.get("conversation_id")
            
            agent = sessions.get(conv_id)
            if not agent:
                config = LocalAgentConfig(conversation_id=conv_id, skills_paths=[SKILLS_DIR])
                agent = Agent(config=config)
                sessions[conv_id] = agent
                
            # Get grocery list from Grocery List Agent
            prompt_grocery = (
                "The menu is approved! Now run the Grocery List Agent skill: "
                "Extract ingredients and scale quantities by the kid count. "
                "Format as checkbox markdown list."
            )
            response_grocery = await agent.chat(prompt_grocery)
            grocery_text = await response_grocery.text()
            
            # Get recipe summaries
            prompt_recipes = (
                "Now run the Dietitian skill: Detail prep steps and recipes for all planned dishes "
                "in the approved menu in clean markdown."
            )
            response_recipes = await agent.chat(prompt_recipes)
            recipes_text = await response_recipes.text()
            
            resp_payload = {
                "grocery": grocery_text,
                "recipes": recipes_text
            }
            if getattr(agent, "fallback_warning", None):
                resp_payload["notification"] = agent.fallback_warning
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp_payload).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def handle_rate(self, payload):
        recipe_name = payload.get("recipe_name", "")
        rating = payload.get("rating", 3)
        notes = payload.get("notes", "")
        
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
                
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                favorites = json.load(f)
            except Exception:
                favorites = []
                
        # Check if already exists, else append
        exists = False
        for fav in favorites:
            if fav.get("name") == recipe_name:
                fav["rating"] = rating
                fav["notes"] = notes
                exists = True
                break
                
        if not exists:
            favorites.append({
                "id": str(uuid.uuid4())[:8],
                "name": recipe_name,
                "rating": rating,
                "notes": notes
            })
            
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(favorites, f, indent=2)
            
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "success", "favorites": favorites}).encode("utf-8"))

def start_server():
    handler = LunchboxGenieHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Lunchbox Genie backend running at http://localhost:{PORT}")
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    start_server()
