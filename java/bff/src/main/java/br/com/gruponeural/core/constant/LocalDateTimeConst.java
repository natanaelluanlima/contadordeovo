package br.com.gruponeural.core.constant;

import java.time.LocalDateTime;

public class LocalDateTimeConst {

    public static final Integer ANO_MINIMO = 1900;
    public static final Integer MES_JANEIRO = 1;
    public static final Integer DIA_PRIMEIRO = 1;
    public static final Integer HORA_ZERO = 0;
    public static final Integer MINUTO_ZERO = 0;
    public static final Integer SEGUNDO_ZERO = 0;

    public static final LocalDateTime DATA_MINIMA = LocalDateTime.of(LocalDateTimeConst.ANO_MINIMO,
            LocalDateTimeConst.MES_JANEIRO, LocalDateTimeConst.DIA_PRIMEIRO, LocalDateTimeConst.HORA_ZERO,
            LocalDateTimeConst.MINUTO_ZERO, LocalDateTimeConst.SEGUNDO_ZERO);

}