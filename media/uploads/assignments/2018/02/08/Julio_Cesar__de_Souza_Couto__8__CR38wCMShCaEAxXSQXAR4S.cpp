#include <stdio.h>
int main()

{
    float lista_temperaturas[5]={32.5, 15.3, 20.2, 31.5, 40.0};
    float t = 42.7;
    
    lista_temperaturas[4] = t;
    lista_temperaturas[0] = lista_temperaturas[2];
    lista_temperaturas[2] = lista_temperaturas[3];

    printf("[%.2f, %.2f, %.2f]\n", lista_temperaturas[0], lista_temperaturas[2], lista_temperaturas[4]);
    
	
	return 0;
}
