import queue
import tkinter as tk

from streamertool.css_manager import active_css_path, ensure_default_css
from streamertool.server import ServerManager
from streamertool.state import State
from streamertool.twitch_chat import TwitchChat
from streamertool.ui import App, configure_ui_context


STATE = State()
UI_EVENTS: queue.Queue[tuple[str, str]] = queue.Queue()


def main() -> None:
    configure_ui_context(STATE, UI_EVENTS)
    ensure_default_css()
    active_css_path(STATE, "call")
    active_css_path(STATE, "queue")
    active_css_path(STATE, "calendar")
    server_manager = ServerManager(STATE.port, STATE)
    server_manager.start()
    chat = TwitchChat(STATE, UI_EVENTS)
    chat.start()
    root = tk.Tk()
    App(root, chat, server_manager)
    root.mainloop()
    server_manager.stop()


if __name__ == "__main__":
    main()

