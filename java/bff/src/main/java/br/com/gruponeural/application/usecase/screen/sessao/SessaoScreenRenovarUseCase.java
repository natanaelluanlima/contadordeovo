package br.com.gruponeural.application.usecase.screen.sessao;

import br.com.gruponeural.dto.request.sessao.SessaoRenovarRequest;
import br.com.gruponeural.dto.response.sessao.SessaoRenovarResponse;
import io.smallrye.mutiny.Uni;

public interface SessaoScreenRenovarUseCase {

    Uni<SessaoRenovarResponse> renovar(SessaoRenovarRequest request);

}
