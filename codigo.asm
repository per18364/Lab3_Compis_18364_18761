.data
    # Aquí irían las declaraciones de datos si las hubiera

.text
.globl main

main:
    # llamada a simpleFn(137)
    li $a0, 137       # Carga el argumento 137 en $a0
    jal simpleFn      # Llama a simpleFn
    
    # Imprimir el resultado que está en $t2
    move $a0, $t2     # Mueve el resultado a $a0 para imprimir
    li $v0, 1         # Código de syscall para imprimir un entero
    syscall
    
    # Termina el programa (syscall para terminar)
    li $v0, 10
    syscall

simpleFn:
    # Supongamos que x e y se inicializan a algún valor, por ejemplo:
    li $t0, 5       # x = 5
    li $t1, 6       # y = 6
    # Realizar x*y*z
    add $t2, $t0, $t1   # t2 = x+y
    add $t2, $t2, $a0   # t2 = x+y+z (usamos $a0 porque tiene el valor de z)
    
    # En este punto, $t2 tiene el valor de x+y+z
    # Retornamos al main
    jr $ra
