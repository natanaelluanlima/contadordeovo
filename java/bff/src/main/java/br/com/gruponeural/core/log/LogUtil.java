package br.com.gruponeural.core.log;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.jboss.logging.Logger;
import org.jboss.logging.Logger.Level;

import br.com.gruponeural.core.util.JsonUtil;
import br.com.gruponeural.core.util.ListUtil;
import br.com.gruponeural.core.util.StringUtil;

/**
 * Log estruturado (fluente). Use {@link #info()}, {@link #error()}, etc. e encadeie até {@link #build()}.
 */
public final class LogUtil {

    private final State state = new State();

    private LogUtil(Level level) {

        this.state.level = level;

    }

    /**
     * Nível TRACE (só aparece com log min-level TRACE ou categoria ajustada).
     */
    public static LogUtil trace() {

        return new LogUtil(Level.TRACE);

    }

    public static LogUtil debug() {

        return new LogUtil(Level.DEBUG);

    }

    public static LogUtil info() {

        return new LogUtil(Level.INFO);

    }

    public static LogUtil warn() {

        return new LogUtil(Level.WARN);

    }

    public static LogUtil error() {

        return new LogUtil(Level.ERROR);

    }

    public static LogUtil fatal() {

        return new LogUtil(Level.FATAL);

    }

    public LogUtil setClass(Class<?> classType) {

        this.state.classType = classType;
        return this;

    }

    public LogUtil setMethodName(String methodName) {

        this.state.methodName = methodName;
        return this;

    }

    /**
     * Anexa exceção ao log (stack em WARN/ERROR/FATAL). Evite colocar a mesma exceção em {@link #setValues}.
     */
    public LogUtil setThrowable(Throwable throwable) {

        this.state.throwable = throwable;
        return this;

    }

    public LogUtil setValuesName(String... valuesName) {

        this.state.listValueName.clear();
        this.state.listValueName.addAll(Arrays.asList(valuesName));

        return this;

    }

    public LogUtil setValues(Object... values) {

        this.state.listValue.clear();
        this.state.listValue.addAll(Arrays.asList(values));

        return this;

    }

    public LogUtil setText(String... texts) {

        this.state.listText.clear();
        this.state.listText.addAll(Arrays.asList(texts));

        return this;

    }

    public void build() {

        Class<?> owner = this.state.classType != null ? this.state.classType : LogUtil.class;
        Logger logger = Logger.getLogger(owner);
        Level level = this.state.level;

        if (!logger.isEnabled(level)) {
            return;
        }

        String message = this.formatMessage(owner);
        Throwable t = this.state.throwable;

        if (level == Level.TRACE) {
            logger.trace(message);
        } else if (level == Level.DEBUG) {
            logger.debug(message);
        } else if (level == Level.INFO) {
            logger.info(message);
        } else if (level == Level.WARN) {
            if (t != null) {
                logger.warn(message, t);
            } else {
                logger.warn(message);
            }
        } else if (level == Level.ERROR) {
            if (t != null) {
                logger.error(message, t);
            } else {
                logger.error(message);
            }
        } else if (level == Level.FATAL) {
            if (t != null) {
                logger.fatal(message, t);
            } else {
                logger.fatal(message);
            }
        }

    }

    private String formatMessage(Class<?> owner) {

        String log = StringUtil.empty();

        log = log.concat(owner.getName());
        log = log.concat(".");
        log = log.concat(this.state.methodName != null ? this.state.methodName : "?");
        log = log.concat("(");
        log = log.concat(ListUtil.toString(this.state.listValueName));
        log = log.concat(")");
        log = log.concat(": ");
        log = log.concat("[");
        log = log.concat(JsonUtil.toJson(this.state.listValue));
        log = log.concat("]");

        if (this.state.listText.size() > 0) {
            log = log.concat(" | ");
            log = log.concat(ListUtil.toString(this.state.listText));
        }

        return log;

    }

    private static final class State {

        Level level;
        Class<?> classType;
        String methodName;
        Throwable throwable;
        List<String> listText = new ArrayList<>();
        List<String> listValueName = new ArrayList<>();
        List<Object> listValue = new ArrayList<>();

    }

}
