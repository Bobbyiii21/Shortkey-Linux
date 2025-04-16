#!/usr/bin/env python3
import evdev
from evdev import InputDevice, categorize, ecodes
import logging
import json
from datetime import datetime

# Setup logging with debug level
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO level
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
SHORTCUTS_JSON_PATH = "KeyboardShortcut.json"

class KeyboardShortcutRecognizer:
    def __init__(self, shortcuts_file_path):
        """Initialize with the shortcuts file path."""
        self.shortcuts = self._load_shortcuts(shortcuts_file_path)
        self.active_modifiers = set()  # Keep track of currently pressed modifier keys
        self.last_key = None  # Keep track of the last regular key pressed
        self.browser_mode = False  # Track if we're in browser mode
        self.browser_mode_triggered = False  # Track if we've triggered browser mode in this key sequence
        logging.debug(f"Loaded shortcuts: {self.shortcuts}")
        
    def _load_shortcuts(self, file_path):
        """Load the keyboard shortcuts from JSON file."""
        try:
            with open(file_path, 'r') as f:
                shortcuts = json.load(f)
                logging.debug(f"Successfully loaded shortcuts from {file_path}")
                return shortcuts
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error loading shortcuts file: {e}")
            return {}
            
    def is_modifier(self, key_name):
        """Check if the key is a modifier key."""
        is_mod = key_name in ['Win', 'Shift', 'Alt', 'Ctrl']
        logging.debug(f"Checking if {key_name} is modifier: {is_mod}")
        return is_mod
        
    def update_modifiers(self, key_name, key_state):
        """Update the set of active modifiers based on key press/release."""
        if key_state == 1:  # Key pressed
            self.active_modifiers.add(key_name)
            logging.debug(f"Added modifier: {key_name}, current modifiers: {self.active_modifiers}")
            
            # Check for browser mode activation (Ctrl+Win+Alt)
            if len(self.active_modifiers) >= 3 and 'Ctrl' in self.active_modifiers and 'Win' in self.active_modifiers and 'Alt' in self.active_modifiers and not self.browser_mode_triggered:
                self.browser_mode = not self.browser_mode
                self.browser_mode_triggered = True
                print(f"\n{'Entering' if self.browser_mode else 'Exiting'} browser mode")
                if self.browser_mode:
                    print("Available browser shortcuts:")
                    browser_shortcuts = self.shortcuts.get('Browser', {})
                    # Display Ctrl shortcuts
                    ctrl_shortcuts = browser_shortcuts.get('Ctrl', {})
                    for key, shortcut in ctrl_shortcuts.items():
                        if isinstance(shortcut, dict) and 'description' in shortcut:
                            print(f"  Ctrl+{key}: {shortcut['description']}")
                print("------------------------------")
                
        elif key_state == 0 and key_name in self.active_modifiers:  # Key released
            self.active_modifiers.remove(key_name)
            logging.debug(f"Removed modifier: {key_name}, current modifiers: {self.active_modifiers}")
            
            # Reset browser mode trigger when all modifiers are released
            if not self.active_modifiers:
                self.browser_mode_triggered = False
            
    def recognize_shortcut(self, key_name, key_state):
        """
        Recognize keyboard shortcuts based on the active modifiers and current key.
        Returns a tuple of (shortcut_found, description, action) if a shortcut is recognized,
        otherwise returns (None, None, None).
        """
        logging.debug(f"Checking shortcut for key: {key_name}, state: {key_state}")
        logging.debug(f"Current active modifiers: {self.active_modifiers}")
        
        # Always update modifiers, regardless of whether we're checking for shortcuts
        if self.is_modifier(key_name):
            self.update_modifiers(key_name, key_state)
            logging.debug("Key is a modifier, updating modifiers")
            # Don't return here, let the code continue to check for shortcuts
            
        # Only check for shortcuts on key press
        if key_state != 1:
            logging.debug("Skipping shortcut check - not a key press event")
            return None, None, None
            
        # If it's not a modifier, set it as the last key
        if not self.is_modifier(key_name):
            self.last_key = key_name
            logging.debug(f"Set last key to: {key_name}")
            
        # Handle browser mode shortcuts
        if self.browser_mode:
            browser_shortcuts = self.shortcuts.get('Browser', {})
            
            if key_name == 'Esc':
                self.browser_mode = False
                print("\nExiting browser mode")
                print("------------------------------")
                return None, None, None
                
            # Check for Shift+Tab combination
            if key_name == 'Tab' and 'Shift' in self.active_modifiers:
                shortcut = browser_shortcuts.get('Shift+Tab')
                if shortcut:
                    return 'Shift+Tab', shortcut['description'], shortcut['action']
            
            # Check for regular browser shortcuts
            # First check if the key is a modifier
            if self.is_modifier(key_name):
                return None, None, None
                
            # Then check for Ctrl + key combinations
            if 'Ctrl' in self.active_modifiers:
                ctrl_shortcuts = browser_shortcuts.get('Ctrl', {})
                shortcut = ctrl_shortcuts.get(key_name)
                if shortcut:
                    return f"Ctrl+{key_name}", shortcut['description'], shortcut['action']
            
            return None, None, None
            
        # Check for system shortcuts
        system_shortcuts = self.shortcuts.get('System', {})
        current_level = system_shortcuts
        shortcut_name = ""
        
        # First check if we have any active modifiers
        if not self.active_modifiers:
            logging.debug("No active modifiers, checking for single key shortcut")
            if key_name in current_level:
                shortcut_data = current_level[key_name]
                if isinstance(shortcut_data, dict):
                    description = shortcut_data.get("description", "")
                    action = shortcut_data.get("action", None)
                    logging.debug(f"Found single key shortcut: {key_name}, description: {description}, action: {action}")
                    return key_name, description, action
            return None, None, None
            
        # Try to find a matching shortcut by checking each possible modifier order
        def check_shortcut(level, modifiers, key, path=""):
            if not modifiers:
                if key in level:
                    shortcut_data = level[key]
                    if isinstance(shortcut_data, dict):
                        description = shortcut_data.get("description", "")
                        action = shortcut_data.get("action", None)
                        return path + key, description, action
                return None, None, None
                
            for i, modifier in enumerate(modifiers):
                if modifier in level:
                    new_path = path + modifier + "+"
                    new_modifiers = modifiers[:i] + modifiers[i+1:]
                    result = check_shortcut(level[modifier], new_modifiers, key, new_path)
                    if result[0] is not None:
                        return result
            return None, None, None
            
        # Try all possible modifier orders
        modifiers = list(self.active_modifiers)
        shortcut_name, description, action = check_shortcut(current_level, modifiers, key_name)
        
        if shortcut_name:
            logging.debug(f"Found shortcut: {shortcut_name}, description: {description}, action: {action}")
            return shortcut_name, description, action
            
        logging.debug("No matching shortcut found")
        return None, None, None

    def predict_shortcuts(self):
        """Predict potential shortcuts based on current active modifiers."""
        predictions = []
        
        # If in browser mode, show browser shortcuts
        if self.browser_mode:
            browser_shortcuts = self.shortcuts.get('Browser', {})
            ctrl_shortcuts = browser_shortcuts.get('Ctrl', {})
            for key, shortcut in ctrl_shortcuts.items():
                if isinstance(shortcut, dict) and 'description' in shortcut:
                    predictions.append((f"Ctrl+{key}", shortcut['description']))
            return predictions
            
        # Get system shortcuts
        system_shortcuts = self.shortcuts.get('System', {})
        
        # If no modifiers are active, return all single-key shortcuts
        if not self.active_modifiers:
            for key, value in system_shortcuts.items():
                if isinstance(value, dict) and "description" in value:
                    predictions.append((key, value["description"]))
            return predictions
            
        # Try to find shortcuts that match the current modifier combination
        def find_predictions(level, modifiers, path=""):
            if not modifiers:
                for key, value in level.items():
                    if isinstance(value, dict):
                        if "description" in value:
                            predictions.append((path + key, value["description"]))
                        else:
                            find_predictions(value, [], path + key + "+")
            else:
                for i, modifier in enumerate(modifiers):
                    if modifier in level:
                        new_path = path + modifier + "+"
                        new_modifiers = modifiers[:i] + modifiers[i+1:]
                        find_predictions(level[modifier], new_modifiers, new_path)
                        
        find_predictions(system_shortcuts, list(self.active_modifiers))
        return predictions

def get_key_name(key_code):
    """Convert evdev key code to a readable key name."""
    key_map = {
        # Special keys and modifiers
        ecodes.KEY_LEFTCTRL: "Ctrl",
        ecodes.KEY_RIGHTCTRL: "Ctrl",
        ecodes.KEY_LEFTALT: "Alt",
        ecodes.KEY_RIGHTALT: "Alt",
        ecodes.KEY_LEFTSHIFT: "Shift",
        ecodes.KEY_RIGHTSHIFT: "Shift",
        ecodes.KEY_LEFTMETA: "Win",  # Windows/Super key
        ecodes.KEY_RIGHTMETA: "Win",
        
        # Function keys
        ecodes.KEY_F1: "F1",
        ecodes.KEY_F2: "F2",
        ecodes.KEY_F3: "F3",
        ecodes.KEY_F4: "F4",
        ecodes.KEY_F5: "F5",
        ecodes.KEY_F6: "F6",
        ecodes.KEY_F7: "F7",
        ecodes.KEY_F8: "F8",
        ecodes.KEY_F9: "F9",
        ecodes.KEY_F10: "F10",
        ecodes.KEY_F11: "F11",
        ecodes.KEY_F12: "F12",
        
        # Navigation keys
        ecodes.KEY_TAB: "Tab",
        ecodes.KEY_ESC: "Esc",
        ecodes.KEY_HOME: "Home",
        ecodes.KEY_END: "End",
        ecodes.KEY_PAGEUP: "PageUp",
        ecodes.KEY_PAGEDOWN: "PageDown",
        ecodes.KEY_DELETE: "Delete",
        ecodes.KEY_BACKSPACE: "Backspace",
        ecodes.KEY_ENTER: "Enter",
        ecodes.KEY_SPACE: "Space",
        
        # Arrow keys
        ecodes.KEY_UP: "ArrowUp",
        ecodes.KEY_DOWN: "ArrowDown",
        ecodes.KEY_LEFT: "ArrowLeft",
        ecodes.KEY_RIGHT: "ArrowRight",
        
        # Printable keys (letters)
        ecodes.KEY_A: "A",
        ecodes.KEY_B: "B",
        ecodes.KEY_C: "C",
        ecodes.KEY_D: "D",
        ecodes.KEY_E: "E",
        ecodes.KEY_F: "F",
        ecodes.KEY_G: "G",
        ecodes.KEY_H: "H",
        ecodes.KEY_I: "I",
        ecodes.KEY_J: "J",
        ecodes.KEY_K: "K",
        ecodes.KEY_L: "L",
        ecodes.KEY_M: "M",
        ecodes.KEY_N: "N",
        ecodes.KEY_O: "O",
        ecodes.KEY_P: "P",
        ecodes.KEY_Q: "Q",
        ecodes.KEY_R: "R",
        ecodes.KEY_S: "S",
        ecodes.KEY_T: "T",
        ecodes.KEY_U: "U",
        ecodes.KEY_V: "V",
        ecodes.KEY_W: "W",
        ecodes.KEY_X: "X",
        ecodes.KEY_Y: "Y",
        ecodes.KEY_Z: "Z",
    }
    
    key_name = key_map.get(key_code, f"KEY_{key_code}")
    logging.debug(f"Converted key code {key_code} to name: {key_name}")
    return key_name

def print_available_shortcuts(shortcuts, prefix=""):
    """Print all available shortcuts in a readable format."""
    for key, value in shortcuts.items():
        if isinstance(value, dict):
            if "description" in value:
                print(f"{prefix}{key}: {value['description']}")
            else:
                print(f"{prefix}{key}:")
                print_available_shortcuts(value, prefix + "  ")
        else:
            print(f"{prefix}{key}: {value}")

def main():
    try:
        # Initialize shortcut recognizer
        shortcut_recognizer = KeyboardShortcutRecognizer(SHORTCUTS_JSON_PATH)
        
        # Print available shortcuts
        print("\n=== Available Shortcuts ===")
        print_available_shortcuts(shortcut_recognizer.shortcuts)
        print("\n==========================\n")
        
        # Open the keyboard device
        keyboard = evdev.InputDevice('/dev/input/event0')
        print(f"\nMonitoring keyboard: {keyboard.name}")
        print("Press any keys (Ctrl+C to exit)")
        print("==============================\n")
        
        # Monitor keyboard events
        for event in keyboard.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                key_event = categorize(event)
                key_name = get_key_name(key_event.scancode)
                state = "pressed" if key_event.keystate == 1 else "released" if key_event.keystate == 0 else "repeated"
                
                # Print key event
                if key_event.keystate != 2:
                    print(f"Key: {key_name} ({state})")
                    
                    # Show predictions when a key is pressed
                    if key_event.keystate == 1:
                        # Update modifiers first
                        if shortcut_recognizer.is_modifier(key_name):
                            shortcut_recognizer.update_modifiers(key_name, key_event.keystate)
                            
                        predictions = shortcut_recognizer.predict_shortcuts()
                        if predictions:
                            print("\nPossible shortcuts:")
                            for shortcut, description in predictions:
                                print(f"  {shortcut}: {description}")
                            print("------------------------------")
                        elif shortcut_recognizer.is_modifier(key_name):
                            print("\nNo shortcuts available with this modifier combination")
                            print("------------------------------")
                
                # Check for shortcuts
                shortcut_name, description, action = shortcut_recognizer.recognize_shortcut(key_name, key_event.keystate)
                if shortcut_name:
                    print(f"SHORTCUT DETECTED: {shortcut_name}")
                    print(f"Description: {description}")
                    if action:
                        print(f"Action: {action}")
                    print("------------------------------")
                
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    main()