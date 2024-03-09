section .text:
    .loop
    LD DIRECT #STDIN
    ST IMMEDIATE #STDOUT
    CMP IMMEDIATE 10
    JNZ DIRECT .loop
    HLT