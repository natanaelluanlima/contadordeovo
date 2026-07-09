package br.com.gruponeural.core.util;

import java.time.LocalDateTime;

import br.com.gruponeural.core.constant.LocalDateTimeConst;

public class LocalDateTimeUtil {

    public static Boolean isEmpty(LocalDateTime localDateTime) {

        if (ObjectUtil.isNull(localDateTime)) {

            return Boolean.TRUE;

        }

        return localDateTime.equals(LocalDateTimeConst.DATA_MINIMA);

    }

    public static LocalDateTime getNow() {

        return LocalDateTime.now();

    }

    public static LocalDateTime getNowIfEmpty(LocalDateTime localDateTime) {

        if (LocalDateTimeUtil.isEmpty(localDateTime)) {

            return getNow();

        }

        return localDateTime;

    }

}
