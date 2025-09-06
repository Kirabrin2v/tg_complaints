import re


def load_html(path):
    with open(f"text/{path}", encoding="UTF-8") as f:
        content = f.read()
    # Удаляем все комментарии <!-- ... -->
    content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    return content
