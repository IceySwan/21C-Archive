import os
import json
from datetime import datetime
from jinja2 import Template
from collections import defaultdict

ROOT_DIR = "."  # 设置你的根目录
OUTPUT_DIR = "."  # 设置输出目录


def scan_files_hierarchical(root):
    """扫描文件并按三级目录结构组织"""
    hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for dirpath, _, filenames in os.walk(root):
        # 获取相对路径并分割
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            continue

        path_parts = rel_dir.split(os.sep)

        # 确保是三级目录结构
        if len(path_parts) >= 3:
            level1 = path_parts[0]  # 三年时段
            level2 = path_parts[1]  # 具体年份
            level3 = path_parts[2]  # 期数

            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    stat = os.stat(fp)
                    file_info = {
                        "name": f,
                        "rel_path": os.path.relpath(fp, root),
                        "abs_path": os.path.abspath(fp),
                        "size_kb": round(stat.st_size / 1024, 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "extension": os.path.splitext(f)[1].lower()
                    }
                    hierarchy[level1][level2][level3].append(file_info)
                except Exception as e:
                    print(f"Skipped: {fp} ({e})")

    return hierarchy


def generate_json_output(hierarchy, output_path):
    """生成JSON格式的层级目录"""
    # 转换为普通字典以便JSON序列化
    json_data = {}
    for level1, level2_dict in hierarchy.items():
        json_data[level1] = {}
        for level2, level3_dict in level2_dict.items():
            json_data[level1][level2] = {}
            for level3, files in level3_dict.items():
                json_data[level1][level2][level3] = files

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)


def generate_markdown_output(hierarchy, output_path):
    """生成Markdown格式的层级目录"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# 文件目录索引\n\n")

        for level1 in sorted(hierarchy.keys()):
            f.write(f"# {level1}\n\n")

            for level2 in sorted(hierarchy[level1].keys()):
                f.write(f"## {level2}\n\n")

                for level3 in sorted(hierarchy[level1][level2].keys()):
                    f.write(f"### {level3}\n\n")

                    # 过滤PDF文件并生成表格
                    pdf_files = [f for f in hierarchy[level1][level2][level3]
                                 if f['extension'] == '.pdf']

                    if pdf_files:
                        f.write("| 标题 | 路径 | 大小 |\n")
                        f.write("|------|------|------|\n")

                        for file_obj in pdf_files:
                            title = os.path.splitext(file_obj['name'])[0]
                            f.write(
                                f"| {title} | [{file_obj['rel_path']}]({file_obj['rel_path']}) | {file_obj['size_kb']} KB |\n")
                        f.write("\n")
                    else:
                        f.write("暂无PDF文件\n\n")


def generate_html_output(hierarchy, output_path):
    """生成HTML格式的层级目录"""
    html_template = Template("""
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件目录索引</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }
        h2 { color: #34495e; border-bottom: 1px solid #bdc3c7; }
        h3 { color: #7f8c8d; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .no-files { color: #95a5a6; font-style: italic; }
    </style>
</head>
<body>
    <h1>文件目录索引</h1>

    {% for level1, level2_dict in hierarchy.items() %}
        <h1>{{ level1 }}</h1>

        {% for level2, level3_dict in level2_dict.items() %}
            <h2>{{ level2 }}</h2>

            {% for level3, files in level3_dict.items() %}
                <h3>{{ level3 }}</h3>

                {% set pdf_files = files | selectattr('extension', 'equalto', '.pdf') | list %}
                {% if pdf_files %}
                    <table>
                        <thead>
                            <tr>
                                <th>标题</th>
                                <th>路径</th>
                                <th>大小</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for file in pdf_files %}
                                <tr>
                                    <td>{{ file.name | replace('.pdf', '') }}</td>
                                    <td><a href="{{ file.rel_path }}">{{ file.rel_path }}</a></td>
                                    <td>{{ file.size_kb }} KB</td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                {% else %}
                    <p class="no-files">暂无PDF文件</p>
                {% endif %}

            {% endfor %}
        {% endfor %}
    {% endfor %}
</body>
</html>
""")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template.render(hierarchy=hierarchy))


def main():
    """主函数"""
    print("开始扫描文件...")
    hierarchy = scan_files_hierarchical(ROOT_DIR)

    if not hierarchy:
        print("未找到符合三级目录结构的文件")
        return

    # 生成输出文件
    json_path = os.path.join(OUTPUT_DIR, "file_index.json")
    md_path = os.path.join(OUTPUT_DIR, "file_index.md")
    html_path = os.path.join(OUTPUT_DIR, "file_index.html")

    print("生成JSON文件...")
    generate_json_output(hierarchy, json_path)

    print("生成Markdown文件...")
    generate_markdown_output(hierarchy, md_path)

    print("生成HTML文件...")
    generate_html_output(hierarchy, html_path)

    print(f"文件索引生成完成!")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    print(f"HTML: {html_path}")


if __name__ == "__main__":
    main()
