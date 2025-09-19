package com.sd.sd.controller;// src/main/java/com/sd/sd/controller/UserController.java

import com.sd.sd.dto.UserResponseDTO;
import com.sd.sd.entity.Users;
import com.sd.sd.service.UserService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/me")
    public ResponseEntity<UserResponseDTO> getAuthenticatedUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        Users authenticatedUser = (Users) authentication.getPrincipal();

        Users user = userService.findById(authenticatedUser.getId());

        // Converte a entidade Users para o DTO antes de retornar
        UserResponseDTO userDto = new UserResponseDTO(user.getId(), user.getName(), user.getEmail());

        return ResponseEntity.ok(userDto);
    }
}