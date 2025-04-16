#!/bin/bash

# Load necessary modules
modprobe_output=$(sudo modprobe dwc2 2>&1)
if [ $? -ne 0 ]; then
    echo "Error loading dwc2 module: $modprobe_output"
    exit 1
fi

modprobe_output=$(sudo modprobe libcomposite 2>&1)
if [ $? -ne 0 ]; then
    echo "Error loading libcomposite module: $modprobe_output"
    exit 1
fi

# Get the UDC name
UDC=$(ls /sys/class/udc)
if [ -z "$UDC" ]; then
    echo "Error: No UDC found"
    echo "Make sure USB gadget mode is enabled in /boot/firmware/config.txt"
    exit 1
fi

echo "Using UDC: $UDC"

# Remove any existing gadget
if [ -d "/sys/kernel/config/usb_gadget/keyboard" ]; then
    echo "" > /sys/kernel/config/usb_gadget/keyboard/UDC
    rm -rf /sys/kernel/config/usb_gadget/keyboard
fi

# Create gadget
cd /sys/kernel/config/usb_gadget/
mkdir -p keyboard
cd keyboard

# Configure gadget
echo 0x1d6b > idVendor  # Linux Foundation
echo 0x0104 > idProduct # Multifunction Composite Gadget
echo 0x0100 > bcdDevice # v1.0.0
echo 0x0200 > bcdUSB    # USB2

# Create English locale
mkdir -p strings/0x409
echo "fedcba9876543210" > strings/0x409/serialnumber
echo "Raspberry Pi" > strings/0x409/manufacturer
echo "USB Keyboard" > strings/0x409/product

# Create HID function
mkdir -p functions/hid.usb0
echo 1 > functions/hid.usb0/protocol
echo 1 > functions/hid.usb0/subclass
echo 8 > functions/hid.usb0/report_length

# Write report descriptor
echo -ne \\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0 > functions/hid.usb0/report_desc

# Create configuration
mkdir -p configs/c.1/strings/0x409
echo "Config 1: USB Keyboard" > configs/c.1/strings/0x409/configuration
echo 250 > configs/c.1/MaxPower

# Link HID function to configuration
ln -s functions/hid.usb0 configs/c.1/

# Enable gadget on the UDC
echo "$UDC" > UDC

echo "USB gadget configured on $UDC"
echo "You may need to reboot for changes to take effect" 