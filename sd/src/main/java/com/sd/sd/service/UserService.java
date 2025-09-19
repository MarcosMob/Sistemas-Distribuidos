package com.sd.sd.service;

import java.util.List;

import com.sd.sd.entity.Users;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import com.sd.sd.repository.UserRepository;

@Service
public class UserService {
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public UserService(UserRepository userRepository, PasswordEncoder passwordEncoder){
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    public Users registerUser(Users users){
        users.setPassword(passwordEncoder.encode(users.getPassword()));
        return userRepository.save(users);
    }
    public List<Users> getAllUsers(){
        return userRepository.findAll();
    }

    public Users findById(Long id) {
        return userRepository.findById(id).orElseThrow(() -> new RuntimeException("Usuário não encontrado."));
    }
}