//
//  main.c
//  desvio_padrao
//
//  Created by Thiago Ribeiro Nunes on 12/16/16.
//  Copyright © 2016 Thiago Ribeiro Nunes. All rights reserved.
//

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#define MAX 5

int main() {
    
    float p[2][MAX], soma = 0.0, media =0.0, variancia = 0.0, desvioPadrao;
    int i, j;
    
    for (i=0; i<2; i++) {
        for (j=0; j<MAX; j++) {
            printf("Digite a produção do dia %d da usina %d: ", i, j);
            scanf("%f", &p[i][j]);
        }
    }
    

    for (i=0; i<2; i++) {
        for(j=0; j<MAX; j++){
            printf("%.2f | ", p[i][j]);
        }
        printf("\n");
    }
    
    for (i=0; i<2; i++) {
        soma = 0.0;
        for(j=0; j<MAX; j++){
            soma = soma + p[i][j];
        }
        media = soma/MAX;
        printf("Média da usina %d: %.2f GW", i+1, media);
    }
//
//    mediaA = somaA/MAX;
//    mediaB = somaB/MAX;
//    
//    for (i=0; i<MAX; i++) {
//        varianciaA = varianciaA + ((pa[i] - mediaA)*(pa[i] - mediaA));
//        varianciaB = varianciaB + ((pb[i] - mediaB)*(pb[i] - mediaB));
//    }
//    
//    desvioPadraoA = sqrt(varianciaA/MAX);
//    desvioPadraoB = sqrt(varianciaB/MAX);
//    
//    printf("\nProdução média da usina A de %.2f GW com desvio de %.2f GW", mediaA, desvioPadraoA);
//    printf("\nProdução média da usina B de %.2f GW com desvio de %.2f GW", mediaB, desvioPadraoB);
//
//

    return 0;
}
