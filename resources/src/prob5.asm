section .text:
    LD DIRECT num1
    MUL DIRECT num2
    MUL DIRECT num3
    MUL DIRECT num4
    MUL DIRECT num5
    MUL DIRECT num6
    MUL DIRECT num7
    MUL DIRECT num8
    ST IMMEDIATE ans
    .loop
    REM DIRECT num9
    ADD IMMEDIATE 48
    ST IMMEDIATE #STDOUT
    LD DIRECT ans
    DIV DIRECT num9
    ST IMMEDIATE ans    
    JNZ DIRECT .loop
    HLT
section .data:
    num1:2
    num2:3
    num3:5
    num4:7
    num5:11
    num6:13
    num7:17
    num8:19
    num9:10
    ans:0