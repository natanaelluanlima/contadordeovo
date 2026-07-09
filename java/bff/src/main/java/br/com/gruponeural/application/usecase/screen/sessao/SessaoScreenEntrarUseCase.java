package br.com.gruponeural.application.usecase.screen.sessao;

import br.com.gruponeural.dto.request.sessao.SessaoEntrarRequest;
import br.com.gruponeural.dto.response.sessao.SessaoEntrarResponse;
import io.smallrye.mutiny.Uni;

public interface SessaoScreenEntrarUseCase {

    Uni<SessaoEntrarResponse> entrar(SessaoEntrarRequest request);

}
