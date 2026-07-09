package br.com.gruponeural.core.constant;

import java.util.UUID;

import br.com.gruponeural.core.util.UUIDUtil;

public enum AplicativoConst {
    APROVEITE_MAIS(UUIDUtil.toUUID("e5f8f6dc-d1ed-46e3-9f9f-3852803a1d26"));

    private final UUID id;

    AplicativoConst(UUID id) {
        this.id = id;
    }

    public UUID getId() {
        return id;
    }
}
