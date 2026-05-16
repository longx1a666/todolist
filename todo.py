from win10toast import ToastNotifier
from datetime import date, timedelta
import os, json

FILE_PATH = "todo.json"


def load_todos():
    """从JSON文件加载待办事项字典 {日期: [事项]}"""
    if not os.path.exists(FILE_PATH):
        return {}
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 兼容旧格式（列表 -> 字典）
    if isinstance(data, list):
        todos_dict = {}
        for item in data:
            d = item.get("created_at", date.today().isoformat())
            todos_dict.setdefault(d, []).append(item)
        data = todos_dict
    # 标准化日期 key 为 YYYY-MM-DD（零补齐），兼容旧数据如 "2026-5-16"
    normalized = {}
    for key, todos in data.items():
        parts = key.split("-")
        if len(parts) == 3:
            norm_key = f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        else:
            norm_key = key
        normalized.setdefault(norm_key, []).extend(todos)
    if normalized != data:
        save_todos(normalized)
    return normalized


def save_todos(todos_dict):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(todos_dict, f, indent=2, ensure_ascii=False)


def add_todo(content, todos_dict):
    today = date.today().isoformat()
    todos_dict.setdefault(today, [])
    todos = todos_dict[today]
    new_id = max([item["id"] for item in todos], default=0) + 1
    new_item = {"id": new_id, "content": content, "done": False}
    todos.append(new_item)
    save_todos(todos_dict)
    print(f"已添加: {content}")


def list_todos(todos_dict, date_str=None):
    if date_str is None:
        date_str = date.today().isoformat()
    todos = todos_dict.get(date_str, [])
    if not todos:
        print(f"{date_str} 没有待办事项。")
        return
    print(f"\n=== {date_str} ===")
    for item in todos:
        status = "done" if item.get("done") else "undone"
        print(f"  {item['id']}. [{status}] {item['content']}")


def mark_done(todo_id, todos_dict):
    for day_todos in todos_dict.values():
        for item in day_todos:
            if item["id"] == todo_id:
                item["done"] = True
                save_todos(todos_dict)
                print(f"已标记完成: {item['content']}")
                return
    print("未找到该项")


def delete_todo(todo_id, todos_dict):
    for day_todos in todos_dict.values():
        for item in day_todos:
            if item["id"] == todo_id:
                day_todos.remove(item)
                save_todos(todos_dict)
                print(f"已删除: {item['content']}")
                return
    print("未找到该项")


def show_yesterday_todos(todos_dict):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    todos = todos_dict.get(yesterday, [])
    undone = [item for item in todos if not item.get("done")]
    if not undone:
        print(f"昨天（{yesterday}）没有未完成的任务。")
        return
    print(f"\n=== 昨天（{yesterday}）未完成的任务 ===")
    for item in undone:
        print(f"  {item['id']}. {item['content']}")


def notify_todos(todos_dict):
    today = date.today().isoformat()
    todos = todos_dict.get(today, [])
    undone = [item for item in todos if not item.get("done")]
    if not undone:
        return
    toaster = ToastNotifier()
    lines = [f"{item['id']}. {item['content']}" for item in undone[:5]]
    if len(undone) > 5:
        lines.append(f"...还有 {len(undone)-5} 项")
    msg = "\n".join(lines)
    toaster.show_toast("今日待办", msg, duration=10, threaded=True)


def main():
    todos_dict = load_todos()

    print("=== 待办事项 CLI 小工具 ===")
    print("可用命令:")
    print("  add <内容>        - 添加待办（自动归入今天）")
    print("  list [日期]       - 列出待办（默认今天，如 list 2026-05-16）")
    print("  done <id>        - 标记完成")
    print("  delete <id>      - 删除")
    print("  yesterday        - 查看昨天未完成")
    print("  quit             - 退出")

    while True:
        cmd = input("> ").strip()
        if not cmd:
            continue
        parts = cmd.split(maxsplit=1)
        action = parts[0].lower()

        if action == "add":
            if len(parts) < 2:
                print("用法: add <内容>")
                continue
            add_todo(parts[1], todos_dict)

        elif action == "list":
            date_str = parts[1] if len(parts) >= 2 else None
            list_todos(todos_dict, date_str)

        elif action == "yesterday":
            show_yesterday_todos(todos_dict)

        elif action == "done":
            if len(parts) < 2:
                print("用法: done <id>")
                continue
            try:
                mark_done(int(parts[1]), todos_dict)
            except ValueError:
                print("id 必须是数字")

        elif action == "delete":
            if len(parts) < 2:
                print("用法: delete <id>")
                continue
            try:
                delete_todo(int(parts[1]), todos_dict)
            except ValueError:
                print("id 必须是数字")

        elif action == "quit":
            print("再见！")
            break

        else:
            print("未知命令。可用命令: add, list, done, delete, yesterday, quit")


if __name__ == "__main__":
    main()
