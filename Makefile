export THEOS = /workspaces/theos
export SDKROOT = /workspaces/theos/sdks/iPhoneOS14.0.sdk

# Corregimos la versión para evitar la advertencia de iOS 9.0
export TARGET = iphone:clang:14.0:14.0
export ARCHS = arm64

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = Luminexx
Luminexx_FILES = Tweak.x

include $(THEOS)/makefiles/tweak.mk
