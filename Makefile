export THEOS = /workspaces/theos
export SDKROOT = $(THEOS)/sdks/iPhoneOS14.5.sdk
export TARGET = iphone:clang:14.5:14.5
# Corregimos la versión para evitar la advertencia de iOS 9.0
export TARGET = iphone:clang:14.0:14.0
export ARCHS = arm64

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = Luminexx
Luminexx_FILES = Tweak.x

include $(THEOS)/makefiles/tweak.mk
