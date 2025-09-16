define AMAZONLINUX_CLOUD_INIT_USER_DATA_TEMPLATE
$(CLOUD_INIT_USER_DATA_TEMPLATE)
endef

# include local overrides if present
-include $(GARDEN_PROJECT_DIR)/.image-garden.local.mk
