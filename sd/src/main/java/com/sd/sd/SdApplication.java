package com.sd.sd;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

@SpringBootApplication
public class SdApplication {

	public static void main(String[] args) {
		BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
        String plainTextPassword = "123456"; // Substitua pela sua senha
        String hashedPassword = encoder.encode(plainTextPassword);
        System.out.println("\n\n\n\n\n\n\n *******************Sua senha criptografada é: " + hashedPassword + "*******************\n\n\n\n\n\n\n");
		SpringApplication.run(SdApplication.class, args);
	}

}
