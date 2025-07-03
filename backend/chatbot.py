import ollama
import json
import os
import sqlite3
import datetime
from typing import List, Dict, Optional
import openai
import anthropic
import google.generativeai as genai
import requests
import uuid

class AIChat:
    def __init__(self):
        self.config = self.load_config()
        self.model = None
        self.current_provider = None
        self.conversation_id = None
        self.initialize_model()
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for chat history"""
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chat_history.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                provider TEXT,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}

    def initialize_model(self):
        """Initialize AI model based on configuration"""
        selected_model = self.config.get('selected_ai_model', '')
        
        # Determine provider and model
        if self.config.get('openai_api_key') and ('gpt' in selected_model.lower() or selected_model.startswith('openai:')):
            self.current_provider = 'openai'
            self.model = selected_model.replace('openai:', '') if selected_model.startswith('openai:') else selected_model
        elif self.config.get('anthropic_api_key') and ('claude' in selected_model.lower() or selected_model.startswith('anthropic:')):
            self.current_provider = 'anthropic'
            self.model = selected_model.replace('anthropic:', '') if selected_model.startswith('anthropic:') else selected_model
        elif self.config.get('google_api_key') and ('gemini' in selected_model.lower() or selected_model.startswith('google:')):
            self.current_provider = 'google'
            self.model = selected_model.replace('google:', '') if selected_model.startswith('google:') else selected_model
        elif self.config.get('ollama_api_key') or selected_model:
            self.current_provider = 'ollama'
            self.model = selected_model
        elif self.config.get('model_path'):
            self.current_provider = 'local'
            self.model = self.config.get('model_path')
        else:
            self.current_provider = None
            self.model = None

    def create_conversation(self, title: str = None) -> str:
        """Create a new conversation and return its ID"""
        conversation_id = str(uuid.uuid4())
        if not title:
            title = f"Chat {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chat_history.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (id, title, provider, model)
            VALUES (?, ?, ?, ?)
        ''', (conversation_id, title, self.current_provider, self.model))
        
        conn.commit()
        conn.close()
        
        self.conversation_id = conversation_id
        return conversation_id

    def save_message(self, conversation_id: str, role: str, content: str):
        """Save a message to the database"""
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chat_history.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
        ''', (conversation_id, role, content))
        
        # Update conversation timestamp
        cursor.execute('''
            UPDATE conversations 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (conversation_id,))
        
        conn.commit()
        conn.close()

    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chat_history.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT role, content, timestamp 
            FROM messages 
            WHERE conversation_id = ? 
            ORDER BY timestamp ASC
        ''', (conversation_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'role': row[0],
                'content': row[1],
                'timestamp': row[2]
            })
        
        conn.close()
        return messages

    def get_conversations_list(self) -> List[Dict]:
        """Get list of all conversations"""
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chat_history.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, provider, model, created_at, updated_at 
            FROM conversations 
            ORDER BY updated_at DESC
        ''')
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'id': row[0],
                'title': row[1],
                'provider': row[2],
                'model': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            })
        
        conn.close()
        return conversations

    def get_response(self, user_input: str, conversation_id: str = None, stream: bool = False):
        """Get AI response with conversation context"""
        if not user_input:
            return "Please provide a message."
        if not self.current_provider:
            return "AI model not configured. Please configure it in the AI Chat settings."

        # Create conversation if none exists
        if not conversation_id:
            conversation_id = self.create_conversation()
        else:
            self.conversation_id = conversation_id

        # Save user message
        self.save_message(conversation_id, 'user', user_input)

        # Get conversation history for context
        history = self.get_conversation_history(conversation_id)
        
        system_prompt = self.config.get('system_prompt', '')
        file_paths = self.config.get('file_paths', [])
        file_contents = ""
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_contents += f"File: {file_path}\n{f.read()}\n\n"
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

        # Build context from history
        context = ""
        if len(history) > 1:  # More than just the current message
            context = "Previous conversation:\n"
            for msg in history[:-1]:  # Exclude the current message
                context += f"{msg['role'].title()}: {msg['content']}\n"
            context += "\n"

        full_prompt = f"{system_prompt}\n\n{file_contents}\n\n{context}User: {user_input}"

        try:
            if self.current_provider == 'openai':
                response = self.get_openai_response(full_prompt, history, stream)
            elif self.current_provider == 'anthropic':
                response = self.get_anthropic_response(full_prompt, history, stream)
            elif self.current_provider == 'google':
                response = self.get_google_response(full_prompt, history, stream)
            elif self.current_provider == 'ollama':
                response = self.get_ollama_response(full_prompt, history, stream)
            elif self.current_provider == 'local':
                response = self.get_local_response(full_prompt, history, stream)
            else:
                response = "Invalid AI model configuration."

            # Save AI response
            if response and not stream:
                self.save_message(conversation_id, 'assistant', response)

            return response
        except Exception as e:
            error_msg = f"Error getting AI response: {e}"
            self.save_message(conversation_id, 'assistant', error_msg)
            return error_msg

    def get_openai_response(self, user_input: str, history: List[Dict], stream: bool = False):
        """Get response from OpenAI GPT models"""
        try:
            api_key = self.config.get('openai_api_key')
            if not api_key:
                return "OpenAI API key not configured."

            # Initialize OpenAI client
            client = openai.OpenAI(api_key=api_key)
            
            # Build messages for OpenAI format
            messages = []
            system_prompt = self.config.get('system_prompt', '')
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history
            for msg in history:
                if msg['role'] in ['user', 'assistant']:
                    messages.append({"role": msg['role'], "content": msg['content']})

            model_name = self.model if self.model else 'gpt-3.5-turbo'
            
            if stream:
                return self._stream_openai_response(client, model_name, messages)
            else:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.7
                )
                return response.choices[0].message.content

        except Exception as e:
            return f"Error with OpenAI API: {e}"

    def get_anthropic_response(self, user_input: str, history: List[Dict], stream: bool = False):
        """Get response from Anthropic Claude models"""
        try:
            api_key = self.config.get('anthropic_api_key')
            if not api_key:
                return "Anthropic API key not configured."

            # This would require the anthropic library
            # For now, return a placeholder
            return f"Anthropic Claude response for: {user_input}"

        except Exception as e:
            return f"Error with Anthropic API: {e}"

    def get_google_response(self, user_input: str, history: List[Dict], stream: bool = False):
        """Get response from Google Gemini models"""
        try:
            api_key = self.config.get('google_api_key')
            if not api_key:
                return "Google API key not configured."

            # This would require the google-generativeai library
            # For now, return a placeholder
            return f"Google Gemini response for: {user_input}"

        except Exception as e:
            return f"Error with Google API: {e}"
    def get_ollama_response(self, user_input: str, history: List[Dict], stream: bool = False):
        """Get response from Ollama models"""
        try:
            # Build context from history
            context = ""
            for msg in history[:-1]:  # Exclude current message
                context += f"{msg['role']}: {msg['content']}\n"
            
            prompt = f"{context}\nuser: {user_input}"
            
            if stream:
                return self._stream_ollama_response(prompt)
            else:
                response = ollama.chat(model=self.model, messages=[
                    {'role': 'user', 'content': prompt}
                ])
                return response['message']['content']

        except Exception as e:
            return f"Error with Ollama: {e}"

    def get_local_response(self, user_input: str, history: List[Dict], stream: bool = False):
        """Get response from local model"""
        try:
            # Placeholder for local model interaction
            return f"Local model response for: {user_input[-50:]}..."
        except Exception as e:
            return f"Error with local model: {e}"

    def _stream_openai_response(self, client, model_name: str, messages: List[Dict]):
        """Stream OpenAI response"""
        try:
            stream = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Error streaming OpenAI response: {e}"

    def _stream_ollama_response(self, prompt: str):
        """Stream Ollama response"""
        try:
            stream = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=True
            )
            
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
                    
        except Exception as e:
            yield f"Error streaming Ollama response: {e}"

    def export_conversation(self, conversation_id: str, format: str = 'json') -> str:
        """Export conversation in specified format"""
        try:
            # Get conversation info
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chat_history.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT title, provider, model, created_at 
                FROM conversations WHERE id = ?
            ''', (conversation_id,))
            
            conv_info = cursor.fetchone()
            if not conv_info:
                return "Conversation not found"
            
            # Get messages
            messages = self.get_conversation_history(conversation_id)
            conn.close()
            
            export_data = {
                'conversation_id': conversation_id,
                'title': conv_info[0],
                'provider': conv_info[1],
                'model': conv_info[2],
                'created_at': conv_info[3],
                'messages': messages
            }
            
            if format.lower() == 'json':
                return json.dumps(export_data, indent=2, ensure_ascii=False)
            elif format.lower() == 'txt':
                text_export = f"Conversation: {conv_info[0]}\n"
                text_export += f"Provider: {conv_info[1]} | Model: {conv_info[2]}\n"
                text_export += f"Created: {conv_info[3]}\n"
                text_export += "=" * 50 + "\n\n"
                
                for msg in messages:
                    text_export += f"{msg['role'].upper()}: {msg['content']}\n"
                    text_export += f"Time: {msg['timestamp']}\n\n"
                
                return text_export
            else:
                return "Unsupported export format"
                
        except Exception as e:
            return f"Error exporting conversation: {e}"

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chat_history.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
            cursor.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models for each provider"""
        models = {
            'openai': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
            'anthropic': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
            'google': ['gemini-pro', 'gemini-pro-vision'],
            'ollama': [],
            'local': []
        }
        
        # Try to get Ollama models
        try:
            ollama_models = ollama.list()
            if 'models' in ollama_models:
                models['ollama'] = [model['name'] for model in ollama_models['models']]
        except:
            pass
        
        # Check for local models
        try:
            models_path = os.path.join(os.path.dirname(__file__), '..', 'models')
            if os.path.exists(models_path):
                local_files = [f for f in os.listdir(models_path) if f.endswith(('.bin', '.gguf', '.ggml'))]
                models['local'] = local_files
        except:
            pass
            
        return models