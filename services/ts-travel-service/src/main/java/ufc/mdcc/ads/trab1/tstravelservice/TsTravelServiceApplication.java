package ufc.mdcc.ads.trab1.tstravelservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

@SpringBootApplication
@EnableCaching
public class TsTravelServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(TsTravelServiceApplication.class, args);
    }
}