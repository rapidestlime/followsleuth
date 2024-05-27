--
-- PostgreSQL database dump
--

-- Dumped from database version 16.3 (Postgres.app)
-- Dumped by pg_dump version 16.1

-- Started on 2024-05-25 22:29:31 +08

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 217 (class 1259 OID 16444)
-- Name: followings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.followings (
    handle_id text,
    following_id text,
    status character varying(3),
    last_updated timestamp without time zone
);


ALTER TABLE public.followings OWNER TO postgres;

--
-- TOC entry 216 (class 1259 OID 16427)
-- Name: handles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.handles (
    handle_id text NOT NULL,
    chat_id bigint,
    handle_uid bigint
);


ALTER TABLE public.handles OWNER TO postgres;

--
-- TOC entry 3629 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN handles.handle_uid; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.handles.handle_uid IS 'unique profile integer ''rest_id''';


--
-- TOC entry 215 (class 1259 OID 16420)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id bigint,
    chat_id bigint NOT NULL,
    user_name text,
    user_email text,
    date_subscribed timestamp without time zone,
    date_end timestamp without time zone,
    comment text
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 3475 (class 2606 OID 16433)
-- Name: handles handles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.handles
    ADD CONSTRAINT handles_pkey PRIMARY KEY (handle_id);


--
-- TOC entry 3473 (class 2606 OID 16426)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (chat_id);


--
-- TOC entry 3477 (class 2606 OID 16449)
-- Name: followings followings_handle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.followings
    ADD CONSTRAINT followings_handle_id_fkey FOREIGN KEY (handle_id) REFERENCES public.handles(handle_id);


--
-- TOC entry 3476 (class 2606 OID 16434)
-- Name: handles handles_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.handles
    ADD CONSTRAINT handles_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.users(chat_id);


-- Completed on 2024-05-25 22:29:33 +08

--
-- PostgreSQL database dump complete
--

