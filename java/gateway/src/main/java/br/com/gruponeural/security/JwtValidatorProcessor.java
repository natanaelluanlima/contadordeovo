package br.com.gruponeural.security;

import java.util.Set;

import org.apache.camel.Exchange;
import org.apache.camel.Processor;

import br.com.gruponeural.core.constant.SessaoConst;
import io.smallrye.jwt.auth.principal.JWTParser;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class JwtValidatorProcessor 
    implements Processor {

    @Inject
    JWTParser jwtParser;

    @Override
    public void process(Exchange exchange) throws Exception {
        String authHeader = exchange.getIn().getHeader("Authorization", String.class);

        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            throw new SecurityException("Token JWT ausente ou inválido.");
        }

        String token = authHeader.substring("Bearer ".length());
        var jwt = jwtParser.parse(token);

        // Se quiser restringir grupos (roles)
        Set<String> groups = jwt.getGroups();
        if (!groups.contains(SessaoConst.SESSAO_USUARIO.getValor())) {
            throw new SecurityException("Usuário não autorizado.");
        }

        // Token é válido — segue a requisição
    }

}
