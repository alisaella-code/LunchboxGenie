# Mock Google Antigravity SDK
import uuid
import urllib.request
import json
import os
import ssl

class LocalAgentConfig:
    def __init__(self, model="gemini-3.5-flash", system_instructions=None, tools=None, capabilities=None, response_schema=None, save_dir=None, conversation_id=None, app_data_dir=None, api_key=None, skills_paths=None):
        self.model = model
        self.system_instructions = system_instructions
        self.tools = tools or []
        self.capabilities = capabilities
        self.response_schema = response_schema
        self.save_dir = save_dir
        self.conversation_id = conversation_id
        self.app_data_dir = app_data_dir
        self.api_key = api_key
        self.skills_paths = skills_paths or []

class CapabilitiesConfig:
    def __init__(self, enable_subagents=True):
        self.enable_subagents = enable_subagents

class TemplatedSystemInstructions:
    def __init__(self, identity=None):
        self.identity = identity

class CustomSystemInstructions:
    def __init__(self, text=None):
        self.text = text

# Create types module namespace mock
class TypesNamespace:
    CapabilitiesConfig = CapabilitiesConfig
    TemplatedSystemInstructions = TemplatedSystemInstructions
    CustomSystemInstructions = CustomSystemInstructions

types = TypesNamespace()

class ToolContext:
    def __init__(self):
        self._state = {}
    def get_state(self, key, default=None):
        return self._state.get(key, default)
    def set_state(self, key, value):
        self._state[key] = value

class Response:
    def __init__(self, text_content):
        self._text = text_content
    
    async def text(self) -> str:
        return self._text
    
    async def structured_output(self) -> dict:
        try:
            text = self._text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
        except Exception:
            return json.loads(self._text)

    def __aiter__(self):
        # Async iteration support for tokens
        async def generator():
            # Split the text into words/chunks
            chunks = self._text.split(" ")
            for i, chunk in enumerate(chunks):
                suffix = " " if i < len(chunks) - 1 else ""
                yield chunk + suffix
        return generator()

    @property
    def thoughts(self):
        async def generator():
            yield "Lunchbox Genie is formulating the perfect lunch box schedule..."
            yield "\nEnsuring nutritional balance..."
            yield "\nDouble-checking allergies..."
        return generator()

class Agent:
    def __init__(self, config=None):
        self.config = config or LocalAgentConfig()
        self.conversation_id = self.config.conversation_id or str(uuid.uuid4())
        self.save_dir = self.config.save_dir or os.path.join(os.path.expanduser("~"), ".gemini", "antigravity", "conversations")
        os.makedirs(self.save_dir, exist_ok=True)
        self.history_file = os.path.join(self.save_dir, f"history_{self.conversation_id}.json")
        self.history = self._load_history()
        self.skills = self._load_skills()

    def _load_skills(self):
        loaded_skills = []
        skills_paths = getattr(self.config, "skills_paths", [])
        if not skills_paths:
            return loaded_skills

        for path in skills_paths:
            expanded_path = os.path.abspath(os.path.expanduser(path))
            if not os.path.exists(expanded_path):
                print(f"[Warning] Skill path does not exist: {expanded_path}")
                continue

            if os.path.isdir(expanded_path):
                skill_file = os.path.join(expanded_path, "SKILL.md")
                if os.path.isfile(skill_file):
                    skill_data = self._parse_skill_file(skill_file)
                    if skill_data:
                        loaded_skills.append(skill_data)
                else:
                    for child in os.listdir(expanded_path):
                        child_path = os.path.join(expanded_path, child)
                        if os.path.isdir(child_path):
                            child_skill_file = os.path.join(child_path, "SKILL.md")
                            if os.path.isfile(child_skill_file):
                                skill_data = self._parse_skill_file(child_skill_file)
                                if skill_data:
                                    loaded_skills.append(skill_data)
            elif os.path.isfile(expanded_path) and os.path.basename(expanded_path) == "SKILL.md":
                skill_data = self._parse_skill_file(expanded_path)
                if skill_data:
                    loaded_skills.append(skill_data)
        
        for skill in loaded_skills:
            print(f"[Antigravity SDK] Loaded skill: '{skill['name']}' from {skill['path']}")
            
        return loaded_skills

    def _parse_skill_file(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            name = os.path.basename(os.path.dirname(filepath))
            description = ""
            body = content
            
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1]
                    body = parts[2].strip()
                    
                    for line in frontmatter_text.splitlines():
                        if ":" in line:
                            key, val = line.split(":", 1)
                            key = key.strip().lower()
                            val = val.strip().strip("'\"")
                            if key == "name":
                                name = val
                            elif key == "description":
                                description = val
                                
            return {
                "name": name,
                "description": description,
                "path": filepath,
                "content": body
            }
        except Exception as e:
            print(f"[Error] Failed to parse skill file {filepath}: {e}")
            return None

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def chat(self, prompt: str) -> Response:
        self.history.append({"role": "user", "parts": [{"text": prompt}]})
        self._save_history()
        
        # Check for real API key
        api_key = self.config.api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set. Please add a valid key to your .env file or configuration.")
            
        model = self.config.model or "gemini-3.5-flash"
        self.fallback_warning = None
        
        try:
            return await self._call_api(model, api_key)
        except Exception as e1:
            if model == "gemini-3.5-flash":
                print(f"[Warning] Gemini 3.5 Flash failed: {e1}. Falling back to Gemini 2.5 Flash...")
                try:
                    res = await self._call_api("gemini-2.5-flash", api_key)
                    self.fallback_warning = "Gemini 3.5 Flash is experiencing high demand. Automatically fell back to Gemini 2.5 Flash."
                    return res
                except Exception as e2:
                    raise RuntimeError(f"Gemini API call failed for both gemini-3.5-flash and gemini-2.5-flash. Errors: [3.5: {e1}] [2.5: {e2}]")
            else:
                raise RuntimeError(f"Gemini API call failed for {model}: {e1}")

    async def _call_api(self, model: str, api_key: str) -> Response:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        system_instruction = None
        if self.config.system_instructions:
            inst = self.config.system_instructions
            if hasattr(inst, "identity"):
                system_instruction = inst.identity
            elif hasattr(inst, "text"):
                system_instruction = inst.text
            else:
                system_instruction = str(inst)
        
        if self.skills:
            skills_instructions = "\n\n## Available Agent Skills\n"
            for skill in self.skills:
                skills_instructions += f"\n### Skill: {skill['name']}\n"
                skills_instructions += f"Description: {skill['description']}\n"
                skills_instructions += f"Instructions:\n{skill['content']}\n"
            if system_instruction:
                system_instruction += skills_instructions
            else:
                system_instruction = skills_instructions
        
        # Format request body for the Gemini API
        formatted_history = []
        for turn in self.history:
            formatted_history.append({
                "role": "user" if turn["role"] == "user" else "model",
                "parts": [{"text": turn["parts"][0]["text"]}]
            })
        
        payload = {
            "contents": formatted_history
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        
        if self.config.response_schema:
            payload["generationConfig"] = {
                "responseMimeType": "application/json"
            }
            
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            context = ssl._create_unverified_context()
            with urllib.request.urlopen(req, context=context) as res:
                res_data = json.loads(res.read().decode("utf-8"))
                text_resp = res_data["candidates"][0]["content"]["parts"][0]["text"]
                self.history.append({"role": "model", "parts": [{"text": text_resp}]})
                self._save_history()
                return Response(text_resp)
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, "read"):
                try:
                    error_body = e.read().decode("utf-8")
                    err_json = json.loads(error_body)
                    error_msg = err_json.get("error", {}).get("message", error_body)
                except Exception:
                    pass
            raise RuntimeError(error_msg)
