total_aulas = int(input("Digite o total de aulas: "))
faltas = int(input("Digite o Número de faltas: "))

frequencia = ((total_aulas - faltas) /total_aulas) * 100

if frequencia >= 75:
  print("Aprovado")
else:
  print("Reprovado")
