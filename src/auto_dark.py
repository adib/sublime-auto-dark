#!/usr/bin/env python
# coding: utf-8


import sublime
import sublime_plugin


running = False


def plugin_loaded():
    _start()


def plugin_unloaded():
    _stop()


def _has_dark_mode_support():
    pf = sublime.platform()
    if pf == 'osx':
        from distutils.version import LooseVersion as V
        import platform
        if V(platform.mac_ver()[0]) < V('10.14'):
            return False
    elif pf == 'linux':
        return False
    return True


def _start():
    if not _has_dark_mode_support():
        return
    running = True
    _tick()


def _stop():
    running = False


def _tick():
    try:
        if running:
            sublime.set_timeout_async(_tick, _update())
    except Exception as e:
        print('AutoDark: Error(_tick): ', e)
        _stop()


def _update():
    import datetime
    now = datetime.datetime.now()
    _paint()
    # every 5 mins max
    return 60000 * (4 - now.minute % 5) + 1000 * (60 - now.second)


def _paint():
    try:
        pref = sublime.load_settings('Preferences.sublime-settings')
        is_dark = _is_dark_os()
        cs_now = pref.get('color_scheme', 'Monokai.sublime-color-scheme')
        cs_new = pref.get('color_scheme.dark', 'Mariana.sublime-color-scheme') if is_dark else pref.get('color_scheme.light', 'Breakers.sublime-color-scheme')
        theme_now = pref.get('theme', 'Default.sublime-theme')
        theme_new = pref.get('theme.dark', 'Adaptive.sublime-theme') if is_dark else pref.get('theme.light', 'Adaptive.sublime-theme')
        if cs_now != cs_new:
            pref.set('color_scheme', cs_new)
        if theme_now != theme_new:
            pref.set('theme', theme_new)
        if cs_now != cs_new or theme_now != theme_new:
            sublime.save_settings('Preferences.sublime-settings')
    except Exception as e:
        print('AutoDark: Error(_paint): ', e)


def _is_dark_os():
    pf = sublime.platform()
    if pf == 'osx':
        try:
            import subprocess
            status = subprocess.check_output(
                'defaults read -g AppleInterfaceStyle'.split(),
                stderr = subprocess.STDOUT
            ).decode().replace('\n', '')
            return True if status.lower() == 'dark' else False
        except Exception as e:
            # return false when light, don't print an error
            return False
    elif pf == 'windows':
        value = 1 # default to light theme
        try:
            import winreg
            with winreg.ConnectRegistry(
                None,
                winreg.HKEY_CURRENT_USER
            ) as registry:
                with winreg.OpenKey(
                    registry,
                    'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize'
                ) as key:
                    value, value_type = winreg.QueryValueEx(key, 'AppsUseLightTheme')
        except Exception as e:
            print('AutoDark: Error(_is_dark_os("windows")): ', e)
        return not bool(value)
    else:
        return False


class EventListener(sublime_plugin.EventListener):

    def on_activated_async(self, view):
        if not _has_dark_mode_support():
            return
        _paint()
