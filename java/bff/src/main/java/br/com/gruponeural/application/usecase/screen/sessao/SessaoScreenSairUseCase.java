package br.com.gruponeural.application.usecase.screen.sessao;

import br.com.gruponeural.dto.request.sessao.SessaoSairRequest;
import br.com.gruponeural.dto.response.sessao.SessaoSairResponse;
import io.smallrye.mutiny.Uni;

public interface SessaoScreenSairUseCase {

    Uni<SessaoSairResponse> sair(SessaoSairRequest request);

}
