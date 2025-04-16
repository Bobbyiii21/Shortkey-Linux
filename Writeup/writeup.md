# ShortKey: Keyboard Shortcut Trainer - Summary

## Overview
ShortKey is a Python application designed to help users learn and master keyboard shortcuts through real-time monitoring and feedback. It provides an interactive learning experience directly in the terminal by intercepting keyboard input while allowing normal keyboard usage.

## Key Features
- Real-time keyboard input interception
- Configurable shortcuts through JSON
- Special browser control mode (activated by Ctrl+Win+Alt)
- Real-time shortcut prediction and suggestions
- Terminal-based interface

## Development Journey
The project evolved through several key phases:

### Initial Concept
- Originally planned as a hardware-based keyboard emulator
- Shifted to software based solution after realizing difficulties with the Raspberry Pi Model 5's USB gadget mode
- Focused on creating a terminal-based shortcut suggestion system

### Technical Challenges and Solutions
1. **Keyboard Input Monitoring**
   - Implemented using Python's evdev library
   - Created a hashmap/dictionary to map keyboard input to plain text
   - Solved multi-device keyboard issue by specifically targeting event0 device

2. **Shortcut Database**
   - Created comprehensive JSON file containing Windows/Linux and Chrome shortcuts
``` JSON
{
  "System": {
        "Ctrl": {
            "C": {
                "description": "Copy",
                "action": "copy",
                "action_type": "clipboard"
            },
            "V": {
                "description": "Paste",
                "action": "paste",
                "action_type": "clipboard"
            }
        }
    }
}
```
  
   - Implemented matching system to compare user input with shortcut database
   - Added notification system for successful shortcut usage

3. **Feature Development**
   - Basic keyboard input monitoring using evdev
   - Simple shortcut recognition system
   - Terminal-based interface implementation
   - JSON-based configuration system
   - Browser mode functionality
   - Real-time prediction system

4. **Refinement Phase**
   - Optimized shortcut recognition algorithms
   - Enhanced user feedback mechanisms
   - Improved code organization and documentation

## Technical Implementation
- Built using Python 3.x
- Uses evdev for keyboard input handling
- JSON configuration for shortcut definitions
- Modular architecture with separate components for:
  - Keyboard input monitoring
  - Shortcut recognition
  - Browser mode management
  - Real-time prediction

## Skills Developed
- System-level programming with Python
- SSH protocol
- Using Efficient Data Structures to improve program performance
- Input device handling and event processing
- Modular software design
- Debugging complex input handling scenarios
- HID signal processing

## Future Plans
- Implementation of a graphical user interface
- Expansion to support more applications
- Development of a learning analytics system
- Raspberry Pi USB keyboard emulation for Windows/MacOS
- Suggestion ranking system

## Compatibility
- Tested on Raspberry Pi 5
- Requires Python 3.x
- Dependencies: evdev, logging, json
