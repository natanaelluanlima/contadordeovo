package br.com.gruponeural.core.util;

import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.core.dto.request.PageRequest;
import br.com.gruponeural.core.enumerator.ExceptionMesangemTipoEnum;
import br.com.gruponeural.core.factory.ExceptionFactory;

public final class PageRequestUtil {

    private PageRequestUtil() {
    }

    public static void validarPagina(PageRequest<?> pageRequest, Class<?> callerClass) {

        LogUtil
            .info()
            .setClass(callerClass)
            .setMethodName("validarPagina")
            .setValuesName("pageRequest")
            .setValues(pageRequest)
            .build();

        if (pageRequest.getOffset() > PageRequest.MAX_OFFSET) {
            throw ExceptionFactory
                .badRequestException(
                    ExceptionMesangemTipoEnum.AVISO,
                    "Combinação de página e tamanho excede o limite suportado.",
                    "")
                .get();
        }

        if (pageRequest.getContent() == null) {
            throw ExceptionFactory
                .badRequestException(
                    ExceptionMesangemTipoEnum.AVISO,
                    "content é obrigatório.",
                    "")
                .get();
        }

    }

}
