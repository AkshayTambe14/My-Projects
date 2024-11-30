#include <stdio.h>
#include <math.h>
#include <stdlib.h>

int fact(float value);
float toRadians(float value);
float taylorSeries(int sinOrCos,float value);
float sine(float value);
float cosine(float value);
float tangent(float value);

int main(int argc, char* argv[]){
	if (argc < 2) {
		printf("Usage: %s <angle_in_degrees>\n", argv[0]);
		return 1;
		}
	float angle = atof(argv[1]);
	float sResult = sine(angle);
	float cResult = cosine(angle);
	float tResult = tangent(angle);
	printf("Sin: %f",sResult);
	printf("\nCos: %f",cResult);
	printf("\nTan: %f",tResult);
	printf("\n");
	return 0;
}

int fact(float value){
	if (value == 0 || value == 1){return 1;}
	else{return value*fact(value-1);}
}

float toRadians(float value){
	float pi = 3.14159265;
	return (value/180.0)*pi;
}

float taylorSeries(int sinOrCos,float value){
	float sign = -1.0f;
    float valuePH = (sinOrCos == 1) ? value: 1.0f;
	if (sinOrCos == 1){
		for (int i = 3; i < 14; i += 2){
			valuePH += sign*(pow(value,i))/fact(i);
			sign *= -1.0f;
		}
	}

	else if (sinOrCos == 2){
		for (int j = 2 ;j < 15; j +=2){
			valuePH += sign*(pow(value,j))/fact(j);
			sign *= -1.0f;
		}
	}
	return valuePH;
}

float sine(float value){
	value = toRadians(value);
	return taylorSeries(1,value);
}

float cosine(float value){
	value = toRadians(value);
	return taylorSeries(2,value);
}

float tangent(float value){
	float c = cosine(value);
	if (c == 0){
		printf("Division by 0, not possible!");
		return INFINITY;
	}
	return sine(value)/c;
}
