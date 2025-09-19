package com.sd.sd.repository;


import java.util.Optional;

import com.sd.sd.entity.Users;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<Users, Long> {
    Optional<Users> findByEmail(String email);
} 
    

