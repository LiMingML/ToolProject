import os
import platform
import stat
import json
import sys

import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置中文字体（根据系统自动选择）
system_name = platform.system()
if system_name == 'Windows':
    plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows系统
elif system_name == 'Darwin':
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # MacOS系统
else:
    plt.rcParams['font.sans-serif'] = ['Droid Sans Fallback']  # Linux系统

plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


def load_exclude_config(config_path):
    """加载排除配置（返回文件夹名称列表）"""
    if not os.path.exists(config_path):
        return set()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            exclude_folders = config.get('exclude_folders', [])
            # 转换为小写进行不区分大小写的匹配（Windows适用）
            if platform.system() == 'Windows':
                return {f.lower() for f in exclude_folders}
            return set(exclude_folders)
    except Exception as e:
        print(f"配置文件解析错误: {e}")
        return set()


def is_hidden(filepath):
    """判断文件是否为隐藏文件（跨平台）"""
    name = os.path.basename(filepath)
    if name.startswith('.'):
        return True
    try:
        if platform.system() == 'Windows':
            attrs = os.stat(filepath).st_file_attributes
            return attrs & stat.FILE_ATTRIBUTE_HIDDEN
        else:
            return False
    except:
        return False


def analyze_folder(folder_path, exclude_folders):
    """分析文件夹并返回统计结果"""
    total_files = 0
    file_types = {}
    hidden_files = 0
    file_sizes = []

    # 处理大小写敏感性
    case_sensitive = platform.system() not in ['Windows', 'Darwin']
    exclude_set = {f.lower() for f in exclude_folders} if not case_sensitive else exclude_folders

    for root, dirs, files in os.walk(folder_path, topdown=True):
        # 排除指定名称的文件夹
        dirs[:] = [d for d in dirs
                   if (d if case_sensitive else d.lower()) not in exclude_set]

        for file in files:
            file_path = os.path.join(root, file)

            # 统计文件类型
            ext = os.path.splitext(file)[1].lower()
            ext = ext[1:] if ext else '无扩展名'
            file_types[ext] = file_types.get(ext, 0) + 1

            # 统计隐藏文件
            if is_hidden(file_path):
                hidden_files += 1

            # 统计文件大小
            try:
                size = os.path.getsize(file_path)
                file_sizes.append((file_path, size))
                total_files += 1  # 只有成功获取大小的文件才计数
            except OSError:
                pass  # 忽略无法访问的文件

    # 获取最大的10个文件
    sorted_files = sorted(file_sizes, key=lambda x: x[1], reverse=True)
    top_10 = sorted_files[:10]

    return {
        'total_files': total_files,
        'file_types': file_types,
        'hidden_files': hidden_files,
        'top_10': top_10
    }




def convert_size(size_bytes):
    """将字节转换为可读格式"""
    units = ('B', 'KB', 'MB', 'GB', 'TB')
    if size_bytes == 0:
        return '0B'
    for unit in units:
        if size_bytes < 1024:
            break
        size_bytes /= 1024
    return f"{size_bytes:.1f} {unit}"




def visualize_results(results):
    """可视化统计结果"""
    total_files = results['total_files']
    hidden_files = results['hidden_files']
    file_types = results['file_types']
    top_10 = results['top_10']

    plt.figure(figsize=(15, 12))
    plt.suptitle("文件夹分析报告", fontsize=16, y=1.02)

    # 基本信息显示
    ax1 = plt.subplot2grid((3, 2), (0, 0), colspan=2)
    ax1.axis('off')
    info_text = f"总文件数: {total_files}\n隐藏文件数: {hidden_files}"
    ax1.text(0.1, 0.5, info_text, fontsize=12, va='center')

    # 文件类型分布
    ax2 = plt.subplot2grid((3, 2), (1, 0))
    sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
    top_types = sorted_types[:8]
    other_count = sum(x[1] for x in sorted_types[8:])
    if other_count > 0:
        top_types.append(('其他', other_count))

    labels = [x[0] for x in top_types]
    sizes = [x[1] for x in top_types]
    ax2.pie(sizes, labels=labels, autopct='%1.1f%%')
    ax2.set_title('文件类型分布')

    # 文件大小TOP10
    ax3 = plt.subplot2grid((3, 2), (1, 1), rowspan=2)
    file_names = [os.path.basename(f[0]) for f in top_10]
    file_paths = [f[0] for f in top_10]
    sizes_mb = [f[1] / 1024 / 1024 for f in top_10]

    bars = ax3.barh(range(len(top_10)), sizes_mb, height=0.6)
    ax3.set_yticks(range(len(top_10)))
    ax3.invert_yaxis()
    ax3.set_xlabel('文件大小 (MB)')
    ax3.set_title('最大的10个文件')

    # 添加完整路径提示
    for i, bar in enumerate(bars):
        ax3.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                 f' {convert_size(top_10[i][1])}\n{file_paths[i]}',
                 va='center', ha='left', fontsize=8)

    # 类型数量柱状图
    ax4 = plt.subplot2grid((3, 2), (2, 0))
    ax4.bar(labels, sizes)
    plt.xticks(rotation=45, ha='right')
    ax4.set_title('各类型文件数量')
    ax4.set_ylabel('数量')

    plt.tight_layout()
    plt.show()

def main():
    # folder_path = input("请输入要分析的文件夹路径：")
    folder_path = '/Users/li/资料'
    if not os.path.isdir(folder_path):
        print("无效的文件夹路径！")
        return

    config_path = 'exclude.json'
    exclude_folders = load_exclude_config(config_path) if config_path.strip() else set()

    results = analyze_folder(folder_path, exclude_folders)
    visualize_results(results)


if __name__ == "__main__":
    main()