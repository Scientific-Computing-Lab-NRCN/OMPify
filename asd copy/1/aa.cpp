#include <string>
#include <omp.h>
typedef int AA;



int main()
{
        AA a;
        int N = 10000;
        int arr[N];

        int sum = 0;

        #pragma omp parallel for
         for(int i = 0; i < N; i++) 
         #pragma omp parallel for    
        for(int i = 0; i < N; i++)
            if(arr[i] > 0){
                sum += arr[i];
            }

          sum = 1000;
}