.data
prompt1: .asciiz "Ingrese el primer numero: "
prompt2: .asciiz "Ingrese el segundo numero: "
result:  .asciiz "El MCD es: "

.text
main:
    # Imprimir mensaje para el primer número
    li   $v0, 4
    la   $a0, prompt1
    syscall

    # Leer el primer número
    li   $v0, 5
    syscall
    move $t0, $v0  # $t0 almacena el primer número

    # Imprimir mensaje para el segundo número
    li   $v0, 4
    la   $a0, prompt2
    syscall

    # Leer el segundo número
    li   $v0, 5
    syscall
    move $t1, $v0  # $t1 almacena el segundo número

    # Calcular MCD
    jal  euclides

    # Imprimir "El MCD es:"
    li   $v0, 4
    la   $a0, result
    syscall

    # Imprimir resultado
    move $a0, $t3  # Usamos $t3 para almacenar el resultado
    li   $v0, 1
    syscall

    # Terminar programa
    li   $v0, 10
    syscall

euclides:
    # Calcula MCD usando el algoritmo de Euclides
    # Entrada: $t0 y $t1
    # Salida: $t3

    # Verificar si $t1 es 0
    beq  $t1, $zero, end_euclides

    # Calcula $t0 % $t1
    div  $t0, $t1
    mfhi $t2      # $t2 = $t0 % $t1

    move $t0, $t1
    move $t1, $t2

    j euclides

end_euclides:
    move $t3, $t0
    jr   $ra
