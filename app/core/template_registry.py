"""
Template registry for managing document templates.
Handles storage, retrieval, and management of default and custom templates.
"""

import logging
from typing import Dict, List, Optional
from app.models import (
    DocumentTemplate,
    DocumentCategory,
    CountryCode,
    DEFAULT_TEMPLATES
)

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """Manages document templates"""

    def __init__(self):
        """Initialize template registry with default templates"""
        self.templates: Dict[str, DocumentTemplate] = DEFAULT_TEMPLATES.copy()
        self.user_templates: Dict[str, DocumentTemplate] = {}

        logger.info(f"Initialized template registry with {len(self.templates)} default templates")

    def register_template(
        self,
        template: DocumentTemplate,
        user_id: Optional[str] = None
    ) -> str:
        """
        Register a new template.

        Args:
            template: Template to register
            user_id: Optional user ID for custom templates

        Returns:
            Template ID

        Raises:
            ValueError: If template_id already exists
        """
        template.custom = True

        if user_id:
            key = f"{user_id}_{template.template_id}"
            if key in self.user_templates:
                raise ValueError(f"Template {key} already exists")
            self.user_templates[key] = template
            logger.info(f"Registered custom template: {key}")
        else:
            if template.template_id in self.templates:
                raise ValueError(f"Template {template.template_id} already exists")
            self.templates[template.template_id] = template
            logger.info(f"Registered template: {template.template_id}")

        return template.template_id

    def get_template(
        self,
        template_id: str,
        user_id: Optional[str] = None
    ) -> Optional[DocumentTemplate]:
        """
        Retrieve template by ID.

        Args:
            template_id: Template identifier
            user_id: Optional user ID for custom templates

        Returns:
            DocumentTemplate or None if not found
        """
        if user_id:
            user_key = f"{user_id}_{template_id}"
            if user_key in self.user_templates:
                return self.user_templates[user_key]

        return self.templates.get(template_id)

    def list_templates(
        self,
        category: Optional[DocumentCategory] = None,
        country: Optional[CountryCode] = None,
        user_id: Optional[str] = None,
        include_custom: bool = True
    ) -> List[DocumentTemplate]:
        """
        List templates with optional filtering.

        Args:
            category: Filter by document category
            country: Filter by country
            user_id: Include user's custom templates
            include_custom: Include custom templates

        Returns:
            List of DocumentTemplates
        """
        templates = list(self.templates.values())

        if user_id and include_custom:
            user_templates = [
                t for k, t in self.user_templates.items()
                if k.startswith(f"{user_id}_")
            ]
            templates.extend(user_templates)

        # Apply filters
        if category:
            templates = [t for t in templates if t.category == category]

        if country:
            templates = [t for t in templates if t.country == country]

        return templates

    def update_template(
        self,
        template_id: str,
        updated_template: DocumentTemplate,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Update existing template.

        Args:
            template_id: Template to update
            updated_template: New template data
            user_id: User ID for custom templates

        Returns:
            True if updated, False if not found

        Raises:
            ValueError: If trying to update default template
        """
        if user_id:
            key = f"{user_id}_{template_id}"
            if key in self.user_templates:
                self.user_templates[key] = updated_template
                logger.info(f"Updated template: {key}")
                return True
            return False

        if template_id in self.templates:
            # Don't allow updating default templates
            if not self.templates[template_id].custom:
                raise ValueError("Cannot update default templates")
            self.templates[template_id] = updated_template
            logger.info(f"Updated template: {template_id}")
            return True

        return False

    def delete_template(
        self,
        template_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Delete custom template.

        Args:
            template_id: Template to delete
            user_id: User ID for custom templates

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If trying to delete default template
        """
        if user_id:
            key = f"{user_id}_{template_id}"
            if key in self.user_templates:
                del self.user_templates[key]
                logger.info(f"Deleted template: {key}")
                return True
            return False

        if template_id in self.templates:
            if not self.templates[template_id].custom:
                raise ValueError("Cannot delete default templates")
            del self.templates[template_id]
            logger.info(f"Deleted template: {template_id}")
            return True

        return False

    def get_template_by_category_and_country(
        self,
        category: DocumentCategory,
        country: CountryCode
    ) -> Optional[DocumentTemplate]:
        """
        Get default template by category and country.

        Args:
            category: Document category
            country: Country code

        Returns:
            DocumentTemplate or None
        """
        for template in self.templates.values():
            if template.category == category and template.country == country:
                return template

        logger.warning(f"No template found for {category} in {country}")
        return None

    def search_templates(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> List[DocumentTemplate]:
        """
        Search templates by name, description, or tags.

        Args:
            query: Search query
            user_id: Include user's custom templates

        Returns:
            List of matching templates
        """
        all_templates = list(self.templates.values())

        if user_id:
            user_templates = [
                t for k, t in self.user_templates.items()
                if k.startswith(f"{user_id}_")
            ]
            all_templates.extend(user_templates)

        query_lower = query.lower()
        results = []

        for template in all_templates:
            # Search in name, description, and tags
            if (
                query_lower in template.template_name.lower() or
                query_lower in template.description.lower() or
                (template.tags and any(query_lower in tag.lower() for tag in template.tags))
            ):
                results.append(template)

        logger.info(f"Search '{query}' found {len(results)} templates")
        return results

    def get_stats(self) -> Dict:
        """
        Get template registry statistics.

        Returns:
            Dict with statistics
        """
        stats = {
            "total_templates": len(self.templates) + len(self.user_templates),
            "default_templates": len(self.templates),
            "custom_templates": len(self.user_templates),
            "by_category": {},
            "by_country": {}
        }

        all_templates = list(self.templates.values()) + list(self.user_templates.values())

        for template in all_templates:
            # Count by category
            cat = template.category.value
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1

            # Count by country
            country = template.country.value
            stats["by_country"][country] = stats["by_country"].get(country, 0) + 1

        return stats


# Global registry instance
_registry: Optional[TemplateRegistry] = None


def get_template_registry() -> TemplateRegistry:
    """Get global template registry instance"""
    global _registry
    if _registry is None:
        _registry = TemplateRegistry()
    return _registry
