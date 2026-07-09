package br.com.gruponeural.core.util;

import java.util.UUID;

public class UUIDUtil {

    public static String getEmptyString() {

        return StringUtil.empty();

    }

    public static Boolean containsStringId(String uuid) {

        return !StringUtil.isEmpty(uuid);

    }

    public static UUID get() {

        return UUID.randomUUID();

    }

    public static String getString() {

        return get().toString();

    }

    public static UUID toUUID(String uuid) {

        return UUID.fromString(uuid);

    }

    public static String toString(UUID uuid) {

        return uuid.toString();

    }

}
