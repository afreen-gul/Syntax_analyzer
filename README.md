# 📘 W++ Compiler Construction Project

## 👨‍💻 Author
**Name:** Afreen Gul  
**Course:** Compiler Construction  
**Project:** W++ Language Compiler  

---

## 📌 Project Overview

The **W++ Compiler** is a mini compiler built for educational purposes to demonstrate the fundamental phases of compiler design. It processes a custom-designed language called **W++**, which is simplified for learning compiler concepts.

This project simulates how real programming languages are compiled step-by-step.

---

▶️ How to Run the Project
1. Clone the Repository
git clone https://github.com/your-username/wpp-compiler.git
cd wpp-compiler
2. Install Dependencies
pip install flask
3. Run the Application
python app.py
4. Open in Browser
http://127.0.0.1:5000/

## 🚀 Features

- Lexical Analysis (Tokenization)
- Syntax Analysis (Parsing)
- Semantic Validation (Basic checks)
- Error Detection and Reporting
- Rule-based compilation pipeline
- Simple custom programming language (W++)

---

## 🧠 Compiler Workflow

Source Code (W++)
↓
Lexical Analyzer (Scanner)
↓
Token Stream
↓
Syntax Analyzer (Parser)
↓
Semantic Analyzer
↓
Output / Error Messages


---

## 📖 W++ Language Rules

### 🔹 Variable Naming Rules

✔ Must start with a letter or underscore  
✔ Can contain letters, digits, underscores  
❌ Cannot start with a number  
❌ Cannot use reserved keywords  

**Examples:**

Valid: x, _count, myVar, var1, total_sum
Invalid: 3x, int, float, if


---

## ❌ Limitations of W++ Language

- No headers (`#include`)
- No standard I/O (`cout`, `cin`)
- No OOP concepts
- No pointers or memory management
- No standard libraries

---

## 🔤 Lexical Analysis

The lexer performs:

- Token generation
- Keyword identification
- Operator detection
- Identifier validation
- Error detection for invalid symbols

### Example Tokens:
x = 10;
→ ID(x), ASSIGN, NUM(10), SEMICOLON

---

## 🧩 Syntax Analysis

The parser checks:

- Correct grammar structure
- Statement correctness
- Sequence validity

### Example Grammar:

statement → id = expression ;
expression → id + id | number


---

## 🧠 Semantic Analysis

Semantic checks include:

- Variable usage validation
- Type consistency (basic level)
- Undefined variable detection

---

## 🧾 Sample W++ Program

```txt
begin
    x = 10;
    y = 20;
    sum = x + y;
end


🛠️ Technologies Used
Python / C++ (Compiler logic)
Flask (optional web interface)
HTML, CSS, JavaScript (frontend UI)
VS Code (Development Environment)

🎯 Learning Outcomes
Understanding compiler design phases
Building a lexical analyzer
Implementing a syntax parser
Learning grammar rules
Handling compilation errors
Designing a mini programming language
📌 Conclusion

The W++ Compiler Project demonstrates how a programming language is processed internally by a compiler. It provides a practical understanding of compiler phases including lexical, syntax, and semantic analysis.

This project serves as a strong foundation for advanced compiler design and programming language development.

⭐ Future Improvements
Add full semantic type checking
Implement intermediate code generation
Add GUI-based compiler interface
Support loops and functions in W++
Optimize parser using LL(1) or LR techniques
