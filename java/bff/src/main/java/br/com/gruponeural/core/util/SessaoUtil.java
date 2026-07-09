package br.com.gruponeural.core.util;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Arrays;
import java.util.HashSet;
import java.util.UUID;

import br.com.gruponeural.core.constant.SessaoConst;
import io.smallrye.jwt.build.Jwt;

public class SessaoUtil {

    public static String gerarChaveAcesso(UUID idPessoa) {
        return Jwt
            .issuer("https://gruponeural.com.br")
            .upn(idPessoa.toString())
            .groups(new HashSet<>(Arrays.asList(SessaoConst.SESSAO_USUARIO.getValor())))
            .expiresAt(Instant.now().plus(15, ChronoUnit.MINUTES))
            .sign();
    }

}
