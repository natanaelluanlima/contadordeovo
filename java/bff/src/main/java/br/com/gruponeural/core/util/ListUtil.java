package br.com.gruponeural.core.util;

import java.util.List;
import java.util.function.Function;

public class ListUtil {

    /**
     * Resultado de {@link #validarLista(Object, Function, Function)}.
     */
    public enum ResultadoValidacaoLista {

        OK,
        /** Objeto ou lista {@code null}, ou lista sem elementos. */
        VAZIA_OU_AUSENTE,
        /** Elemento {@code null} ou {@code campoObrigatorioPorItem} retorna {@code null}. */
        ELEMENTO_INVALIDO

    }

    /**
     * Garante lista com elementos e cada item com campo obrigatório preenchido.
     * Ordem: primeiro ausência/vazio; depois elemento inválido.
     */
    public static <T, U> ResultadoValidacaoLista validarLista(
        T request,
        Function<T, ? extends List<U>> listaDe,
        Function<U, ?> campoObrigatorioPorItem) {

        if (!possuiElementos(request, listaDe)) {
            return ResultadoValidacaoLista.VAZIA_OU_AUSENTE;
        }

        if (possuiItemNuloOuCampoNulo(request, listaDe, campoObrigatorioPorItem)) {
            return ResultadoValidacaoLista.ELEMENTO_INVALIDO;
        }

        return ResultadoValidacaoLista.OK;

    }

    /**
     * {@code true} se a lista não é {@code null} e tem pelo menos um elemento.
     */
    public static boolean possuiElementos(List<?> lista) {

        return lista != null && !lista.isEmpty();

    }

    /**
     * {@code true} se {@code objeto} não é {@code null} e a lista retornada por {@code extrator} possui elementos.
     */
    public static <T> boolean possuiElementos(T objeto, Function<T, ? extends List<?>> extrator) {

        if (objeto == null) {
            return false;
        }

        return possuiElementos(extrator.apply(objeto));

    }

    /**
     * {@code true} se a lista tem pelo menos um item {@code null} ou em que {@code campoObrigatorio} retorna {@code null}.
     * Lista {@code null} ou vazia: {@code false} (nada a invalidar).
     */
    public static <T> boolean possuiItemNuloOuCampoNulo(List<T> lista, Function<T, ?> campoObrigatorio) {

        if (!possuiElementos(lista)) {
            return false;
        }

        return lista.stream().anyMatch(item -> item == null || campoObrigatorio.apply(item) == null);

    }

    /**
     * Mesma regra de {@link #possuiItemNuloOuCampoNulo(List, Function)}, a partir do {@code objeto} e da lista obtida por {@code listaDe}.
     */
    public static <T, U> boolean possuiItemNuloOuCampoNulo(
        T objeto,
        Function<T, ? extends List<U>> listaDe,
        Function<U, ?> campoObrigatorio) {

        if (objeto == null) {
            return false;
        }

        return possuiItemNuloOuCampoNulo(listaDe.apply(objeto), campoObrigatorio);

    }

    public static String toString(List<String> list) {

        return String.join(", ", list);

    }

}

