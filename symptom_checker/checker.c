#include <stdio.h>
#include <string.h>

int main() {
    char input[200];
    fgets(input, sizeof(input), stdin);

    if (strstr(input, "fever") && strstr(input, "cough")) {
        printf("You may have a viral infection.\n");
    } else if (strstr(input, "headache")) {
        printf("Drink water. Could be dehydration or stress.\n");
    } else {
        printf("Consult a doctor for detailed diagnosis.\n");
    }
    return 0;
}
