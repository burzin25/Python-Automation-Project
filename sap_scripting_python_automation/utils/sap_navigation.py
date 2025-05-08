import logging
import time

logger = logging.getLogger(__name__)

def ensure_scroll(session):
    """
    Scrolls the SAP window to bring all elements into view.
    """
    try:
        usr_element = session.FindById("wnd[0]/usr")
        scrollbar = usr_element.verticalScrollbar

        if scrollbar.position < scrollbar.Maximum:
            for _ in range(min(5, scrollbar.Maximum - scrollbar.position)):
                scrollbar.position += 1
                time.sleep(0.1)  # Minimized sleep duration

        logger.info("[✅] Scrolled SAP screen before searching.")

    except Exception as e:
        logger.warning(f"[⚠] Scroll failed: {e}")
