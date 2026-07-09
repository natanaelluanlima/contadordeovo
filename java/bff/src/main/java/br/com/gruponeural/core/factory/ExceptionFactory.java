package br.com.gruponeural.core.factory;

import java.util.function.Supplier;

import br.com.gruponeural.core.enumerator.ExceptionMesangemTipoEnum;
import br.com.gruponeural.core.exception.BadRequestException;
import br.com.gruponeural.core.exception.InternalServerErrorException;
import br.com.gruponeural.core.exception.NotFoundException;
import br.com.gruponeural.core.exception.PersistenceException;
import br.com.gruponeural.core.exception.UnauthorizedException;

public class ExceptionFactory {

    public static Supplier<NotFoundException> notFoundException(ExceptionMesangemTipoEnum mensagemTipo, String mensagemTitulo, String mensagemDetalhe) {

        return () -> new NotFoundException(mensagemTipo, mensagemTitulo, mensagemDetalhe);

    }

    public static Supplier<PersistenceException> persistenceException(ExceptionMesangemTipoEnum mensagemTipo, String mensagemTitulo, String mensagemDetalhe) {

        return () -> new PersistenceException(mensagemTipo, mensagemTitulo, mensagemDetalhe);

    }

    public static Supplier<UnauthorizedException> unauthorizedException(ExceptionMesangemTipoEnum mensagemTipo, String mensagemTitulo, String mensagemDetalhe) {

        return () -> new UnauthorizedException(mensagemTipo, mensagemTitulo, mensagemDetalhe);

    }

    public static Supplier<InternalServerErrorException> internalServerErrorException(ExceptionMesangemTipoEnum mensagemTipo, String mensagemTitulo, String mensagemDetalhe) {

        return () -> new InternalServerErrorException(mensagemTipo, mensagemTitulo, mensagemDetalhe);

    }

    public static Supplier<BadRequestException> badRequestException(ExceptionMesangemTipoEnum mensagemTipo, String mensagemTitulo, String mensagemDetalhe) {

        return () -> new BadRequestException(mensagemTipo, mensagemTitulo, mensagemDetalhe);

    }

}
