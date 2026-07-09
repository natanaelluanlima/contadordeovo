package br.com.gruponeural.application.resource.screen.sessao;

import br.com.gruponeural.dto.request.sessao.SessaoEntrarRequest;
import br.com.gruponeural.dto.request.sessao.SessaoRenovarRequest;
import br.com.gruponeural.dto.request.sessao.SessaoSairRequest;
import br.com.gruponeural.dto.response.sessao.SessaoEntrarResponse;
import br.com.gruponeural.dto.response.sessao.SessaoRenovarResponse;
import br.com.gruponeural.dto.response.sessao.SessaoSairResponse;
import io.smallrye.mutiny.Uni;

public interface SessaoScreenResource {

    Uni<SessaoEntrarResponse> entrar(SessaoEntrarRequest request);

    Uni<SessaoRenovarResponse> renovar(SessaoRenovarRequest request);

    Uni<SessaoSairResponse> sair(SessaoSairRequest request);

}
