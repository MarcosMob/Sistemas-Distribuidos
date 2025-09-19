package com.sd.sd.controller;


import com.sd.sd.dto.AuthenticateDTO;
import com.sd.sd.dto.LoginResponseDTO;
import com.sd.sd.dto.UserResponseDTO;
import com.sd.sd.entity.Users;
import com.sd.sd.security.TokenService;

import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
public class AuthController {
    private final AuthenticationManager authenticationManager;
    private final TokenService tokenService;

    public AuthController(AuthenticationManager authenticationManager, TokenService tokenService) {
        this.authenticationManager = authenticationManager;
        this.tokenService = tokenService;
    }

    @PostMapping("/login")
    public LoginResponseDTO login(@RequestBody AuthenticateDTO data) {
        var usernamePassword = new UsernamePasswordAuthenticationToken(data.email(), data.password());
        var auth = this.authenticationManager.authenticate(usernamePassword);
        var user = (Users) auth.getPrincipal();
        var token = tokenService.generateToken(user);
        return new LoginResponseDTO(token);
    }
}