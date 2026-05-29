# 脚本接口文档

本文档描述了所有脚本的接口、输入参数和输出格式。

## 1. get_cookies.py - Cookie获取服务

### 主要函数

#### `get_cookies_for_user(sid, password, output_file)`

**功能**: 为指定用户获取所有系统的cookies

**输入参数**:
- `sid` (str): 学号
- `password` (str): 密码  
- `output_file` (str, 可选): 输出文件名，默认为 `"data/cookies.json"`

**输出**:
- 返回类型: `Dict[str, Any]`
- 包含CAS、Blackboard、TIS系统的cookies信息
- 自动保存到指定文件

**使用示例**:
```python
from get_cookies import get_cookies_for_user
cookies_data = get_cookies_for_user("12345678", "your_password")
```

---

## 2. bb_course.py - Blackboard课程信息获取

### 主要函数

#### `get_bb_courses(sid, password, cookies_file, term_filter)`

**功能**: 获取Blackboard课程列表

**输入参数**:
- `sid` (str, 可选): 学号（如果提供，会先获取cookies）
- `password` (str, 可选): 密码（如果提供，会先获取cookies）
- `cookies_file` (str, 可选): cookies文件路径，默认为 `"data/cookies.json"`
- `term_filter` (str, 可选): 学期过滤条件，默认为 `"2025秋"`（如"2025秋"、"Fall 2025"）

**输出**:
- 返回类型: `List[Dict[str, str]]` 
- 每个课程包含: `title`, `course_id`, `url`

**使用示例**:
```python
from bb_course import get_bb_courses
courses = get_bb_courses(sid="12345678", password="your_password", term_filter="Fall 2025")
```

#### `get_and_save_courses(sid, password, cookies_file, term_filter, output_file)`

**功能**: 获取并保存课程列表

**输入参数**:
- `sid` (str, 可选): 学号
- `password` (str, 可选): 密码
- `cookies_file` (str, 可选): cookies文件路径，默认为 `"data/cookies.json"`
- `term_filter` (str, 可选): 学期过滤条件，默认为 `"2025秋"`
- `output_file` (str, 可选): 输出文件名，默认为 `"data/courses.json"`

**输出**:
- 返回类型: `List[Dict[str, str]]`
- 自动保存课程列表到文件

---

## 3. tis_schedule.py - TIS课表数据获取


#### `fetch_and_process_schedule(sid, password, cookies_file, raw_output, processed_output)`

**功能**: 获取并处理课表数据

**输入参数**:
- `sid` (str, 可选): 学号
- `password` (str, 可选): 密码
- `cookies_file` (str, 可选): cookies文件路径，默认为 `"data/cookies.json"`
- `raw_output` (str, 可选): 原始数据输出文件名，默认为 `"data/tis_schedule_raw.json"`
- `processed_output` (str, 可选): 处理后数据输出文件名，默认为 `"data/tis_schedule_processed.json"`

**输出**:
- 返回类型: `List[Dict]`
- 处理后的课表数据，包含: `course_name`, `teacher`, `weekday`, `weeks`, `location`, `time_slots`

**使用示例**:
```python
from tis_schedule import fetch_and_process_schedule
schedule = fetch_and_process_schedule(sid="12345678", password="your_password")
```

---

## 4. bb_download.py - Blackboard文件下载

### 主要函数

#### `download_all_courses(sid, password, cookies_file, term_filter)`

**功能**: 下载所有课程的文件

**输入参数**:
- `sid` (str, 可选): 学号（如果提供，会先获取cookies）
- `password` (str, 可选): 密码（如果提供，会先获取cookies）
- `cookies_file` (str, 可选): cookies文件路径，默认为 `"data/cookies.json"`
- `term_filter` (str, 可选): 学期过滤条件，默认为 `"2025秋"`

**输出**:
- 返回类型: `int`
- 下载的文件总数
- 文件保存到 `downloads/` 目录，按课程名称组织

**使用示例**:
```python
from bb_download import download_all_courses
total_files = download_all_courses(sid="12345678", password="your_password")
```

#### `load_courses(sid, password, cookies_file, term_filter)`

**功能**: 加载课程列表，如果文件不存在则自动获取

**输入参数**:
- `sid` (str, 可选): 学号
- `password` (str, 可选): 密码
- `cookies_file` (str, 可选): cookies文件路径，默认为 `"data/cookies.json"`
- `term_filter` (str, 可选): 学期过滤条件，默认为 `"2025秋"`

**输出**:
- 返回类型: `List[Dict]`
- 课程列表

---

## 5. bb_calendar.py - Blackboard日历数据获取

### 主要函数

#### `get_bb_calendar(sid, password, cookies_file, course_id, mode)`

**功能**: 获取Blackboard日历数据

**输入参数**:
- `sid` (str, 可选): 学号（如果提供，会先获取cookies）
- `password` (str, 可选): 密码（如果提供，会先获取cookies）
- `cookies_file` (str, 可选): cookies文件路径，默认为 `"data/cookies.json"`
- `course_id` (str, 可选): 课程ID，空字符串表示所有课程，默认为 `""`
- `mode` (str, 可选): 模式，personal表示个人日历，默认为 `"personal"`

**输出**:
- 返回类型: `List[Dict]`
- 每个事件包含: `id`, `title`, `start`, `end`, `allDay`, `courseId`, `courseName`, `eventType`, `description`, `location`, `url`, `color`, `textColor`, `borderColor`, `backgroundColor`

**使用示例**:
```python
from bb_calendar import get_bb_calendar
calendar_data = get_bb_calendar(sid="12345678", password="your_password")
```


## 6. download_student_photo.py - 学生照片下载

### 主要函数

#### `download_student_photo(rxzp_path, cookies_file, output_dir)`

**功能**: 下载学生照片并返回Base64编码

**输入参数**:
- `rxzp_path` (str, 可选): 照片路径，如果为None则使用默认路径
- `cookies_file` (str, 可选): cookies文件路径，默认为 `"data/cookies.json"`
- `output_dir` (str, 可选): 输出目录，默认为 `"data/photos"`

**输出**:
- 返回类型: `dict`
- 包含Base64数据和文件信息的字典，失败时返回None

**使用示例**:
```python
from download_student_photo import download_student_photo
photo_data = download_student_photo()
```

---

## 7. tis_query.py - TIS学生信息查询

### 主要函数

#### `query_tis_data(sid, password, output_file)`

**功能**: 查询TIS学生信息数据，自动获取cookies并处理数据

**输入参数**:
- `sid` (str): 学号
- `password` (str): 密码
- `output_file` (str, 可选): 输出文件名，默认为 `"data/tis_imfor.json"`

**输出**:
- 返回类型: `Dict`
- 学生信息数据，包含以下字段：
  - 基本信息：学号、姓名、姓名拼音、性别代码、证件号、出生日期、年级代码
  - 院系信息：院系名称（已替换代码为名称）
  - 书院信息：所属书院名称（已替换代码为名称）
  - 班级信息：班级名称（已替换代码为名称）
  - 联系方式：宿舍号、联系电话、电子邮箱
  - 其他：高考成绩等

**特性**:
- 自动获取TIS系统cookies
- 智能数据清理：删除null值和无用字段
- 代码映射：自动将院系代码、书院代码、班级代码替换为对应的名称
- 字段优化：只保留名称字段，删除原始代码字段

**使用示例**:
```python
from tis_query import query_tis_data
student_data = query_tis_data("12345678", "your_password")
```


---

## 数据文件说明

### 输出文件位置
- `data/cookies.json`: 所有系统的cookies
- `data/courses.json`: 课程列表
- `data/tis_schedule_raw.json`: 原始课表数据
- `data/tis_schedule_processed.json`: 处理后的课表数据
- `data/bb_calendar.json`: Blackboard日历数据
- `data/tis_imfor.json`: TIS学生信息数据
- `data/tis_imfor_clean.json`: 清理后的TIS学生信息数据
- `downloads/`: 下载的文件目录

### 环境变量
- `SUSTECH_SID`: 学号
- `SUSTECH_PASSWORD`: 密码
