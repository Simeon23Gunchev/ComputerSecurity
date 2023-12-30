In order to test the functionalities of the program:
1. go to the dist folder and run the server.exe, if you do not have the key.bin file run the server.exe twice
2. open cmd and navigate to the path of the dist folder 
3. type : " client.exe client1.json " and you will get the output

still left the token there, but it can be removed. Also provided the code in case you want to take a look at it. 


The project was made by :

#Alexandra Zamfir i6273294
#Mihaela Stanoeva i6273299
#Anna Nowowiejska i6289598
#Simeon Gunchev i6242650
#Adelin Birzan i6285129

For the fix it phase, vulnerabilities fixed :

1. The client-server communication changed to using SSL encryption.
2. Fixed the No Constraints on the Number of Requests problem
3. Added max number of attempts of a certain client
4. Added token generation for session management for each client
5. Added encryption on client to server messages and made the server decrypt it
6. Handling unsupported data types
7. Basic error handling
8. Handled large data packets sent to the server
9. Password hashing
10. Assure that the amount to be increased or decreased is nonnegative