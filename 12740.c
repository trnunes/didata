#include <stdio.h>



int main(void) {

int V, R, I;



printf("informe o valor da tensao\n");

scanf("%d", &V);

printf("Informe o valor da corrente\n");

scanf("%d", &I);



R = V/I;



if (R>50)

printf("A resistencia e muito alta para o circuito operar");

return 0;

}