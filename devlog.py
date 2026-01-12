import datetime
import os

LOG_FILE = "devlog.md"


def prompt_section(title, multi_line=False):
    print(f"\n=== {title} ===")
    if multi_line:
        print("(输入多行内容，空行结束)")
        lines = []
        while True:
            line = input("> ").strip()
            if line == "":
                break
            lines.append(f"- {line}")
        return "\n".join(lines) if lines else "- （无）"
    else:
        line = input("> ").strip()
        return f"- {line}" if line else "- （无）"


def main():
    date = datetime.date.today().strftime("%Y-%m-%d")

    # 日志模板部分
    print("🧑‍💻 开发日志记录器")
    print(f"日期：{date}\n")

    done = prompt_section("✅ 今天完成", multi_line=True)
    issues = prompt_section("🐛 今天遇到的问题", multi_line=True)
    next_steps = prompt_section("🚀 明天计划", multi_line=True)
    ideas = prompt_section("📝 临时想法 / 灵感", multi_line=True)

    entry = f"""
## 📅 {date}

### ✅ 今天完成
{done}

### 🐛 今天遇到的问题
{issues}

### 🚀 明天计划
{next_steps}

### 📝 临时想法 / 灵感
{ideas}

"""

    # 如果文件不存在，先写标题
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("# 🧑‍💻 开发日志\n")

    # 检查是否已有当天日志
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        if f"## 📅 {date}" in content:
            print(f"❗ 今天的日志 {date} 已经存在，未重复写入。")
            return

    # 追加写入
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"✅ 日志已写入 {LOG_FILE}")


if __name__ == "__main__":
    main()
